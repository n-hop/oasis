import logging
import copy
import os
from abc import ABC, abstractmethod
from typing import List
from core.topology import (ITopology)
from protosuites.proto import IProtoSuite
from interfaces.routing import IRoutingStrategy
from interfaces.host import IHost
from testsuites.test import (ITestSuite)
from var.global_var import g_oasis_root_fs
from tools.util import (is_same_path)


class INetwork(ABC):
    def __init__(self):
        self.id = 0
        self.test_suites = []
        self.proto_suites = []
        self.test_results = {}
        self.is_started_flag = False
        self.is_accessible_flag = True
        self.config_base_path = None

    def is_accessible(self):
        return self.is_accessible_flag

    def get_id(self):
        return self.id

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_hosts(self) -> List[IHost]:
        pass

    @abstractmethod
    def get_num_of_host(self) -> int:
        pass

    @abstractmethod
    def get_host_ip_range(self) -> str:
        pass

    @abstractmethod
    def get_link_table(self):
        pass

    @abstractmethod
    def get_routing_strategy(self) -> IRoutingStrategy:
        pass

    @abstractmethod
    def reload(self, top: ITopology):
        pass

    def is_started(self):
        return self.is_started_flag

    def get_topology_description(self):
        return ""

    def add_protocol_suite(self, proto_suite: IProtoSuite):
        self.proto_suites.append(proto_suite)
        self._load_config_base_path(proto_suite)

    def add_test_suite(self, test_suite: ITestSuite):
        self.test_suites.append(test_suite)

    def perform_test(self):
        """Perform the test for each input case from YAML file
        """
        if self.proto_suites is None or len(self.proto_suites) == 0:
            logging.error("No protocol set")
            return False
        if self.test_suites is None or len(self.test_suites) == 0:
            logging.error("No test suite set")
            return False
        self._install_root_fs()
        # Combination of protocol and test
        for proto in self.proto_suites:
            # start the protocol
            logging.info("Starting protocol %s on network %s",
                         proto.get_config().name, self.get_id())
            if proto.start(self) is False:
                logging.error("Protocol %s failed to start",
                              proto.get_config().name)
                return False
            for test in self.test_suites:
                valid_config = self._check_test_config(proto, test)
                if not valid_config:
                    continue
                # run `test` on `network`(self) specified by `proto`
                logging.info("Running test protocol %s %s",  proto.get_config().name,
                             test.type())
                result = test.run(self, proto)
                if result.is_success is False:
                    logging.error(
                        "Test %s failed, please check the log file %s",
                        test.config.test_name, result.record)
                    return False
                if test.type() not in self.test_results:
                    self.test_results[test.type()] = {}
                    self.test_results[test.type()]['results'] = []
                self.test_results[test.type()]['config'] = copy.deepcopy(
                    test.get_config())
                self.test_results[test.type()]['results'].append(
                    copy.deepcopy(result))
                logging.debug("Added Test result for %s", result.record)
            # stop the protocol
            proto.stop(self)
        return True

    def get_test_results(self):
        return self.test_results

    def reset(self):
        self.proto_suites = []
        self.test_suites = []
        self.test_results = {}

    def _load_config_base_path(self, proto_suite: IProtoSuite):
        if self.config_base_path is None:
            self.config_base_path = proto_suite.get_config().config_base_path

    def _install_root_fs(self) -> bool:
        """Install root fs on all hosts in the network.
        """
        all_hosts = self.get_hosts()
        if all_hosts is None:
            return False
        # from oasis means it is mapped with oasis workspace
        root_fs_from_oasis = g_oasis_root_fs
        # from user means it is mapped by `-p config_folder`
        root_fs_from_user = f"{self.config_base_path}rootfs"
        # root_fs_from_user and root_fs_from_oasis may be the same
        is_same_root_fs = is_same_path(
            root_fs_from_oasis, root_fs_from_user)
        if not os.path.exists(root_fs_from_oasis):
            logging.error("Oasis Root fs not found at %s", root_fs_from_user)
            return False
        if not os.path.exists(root_fs_from_user):
            logging.error("User Root fs not found at %s", root_fs_from_user)
            return False
        for host in all_hosts:
            # user's root fs can overwrite oasis's root fs
            host.cmd("cp -r %s/* /" % root_fs_from_oasis)
            if is_same_root_fs is False:
                host.cmd("cp -r %s/* /" % root_fs_from_user)
                logging.info(
                    "############### Oasis Root fs %s %s installed on %s",
                    root_fs_from_oasis, root_fs_from_user, host.name())
            else:
                logging.info(
                    "############### Oasis Root fs %s installed on %s",
                    root_fs_from_oasis, host.name())
        return True

    def _check_test_config(self, proto: IProtoSuite, test: ITestSuite):
        if not proto.is_distributed():
            proto_conf = proto.get_config()
            if proto_conf is None:
                logging.error("Protocol config is not set")
                return False
            hosts = proto_conf.hosts
            if hosts is None or len(hosts) != 2:
                logging.error(
                    "INetwork Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
                return False
            if hosts[0] != test.config.client_host or \
                    hosts[1] != test.config.server_host:
                logging.error(
                    "Test non-distributed protocols, protocol client/server runs on %s/%s, "
                    "but test tools client/server hosts are %s/%s.",
                    hosts[0], hosts[1],
                    test.config.client_host, test.config.server_host)
                return False
        return True
