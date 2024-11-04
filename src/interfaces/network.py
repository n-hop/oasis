import logging
import copy
from abc import ABC, abstractmethod
from typing import List
from containernet.topology import (ITopology)
from protosuites.proto import IProtoSuite
from interfaces.routing import IRoutingStrategy
from interfaces.host import IHost
from testsuites.test import (ITestSuite)


class INetwork(ABC):
    def __init__(self):
        self.test_suites = []
        self.proto_suites = []
        self.test_results = {}
        self.is_started_flag = False
        self.is_accessible_flag = True

    def is_accessible(self):
        return self.is_accessible_flag

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
        # Combination of protocol and test
        for proto in self.proto_suites:
            # start the protocol
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

    def _check_test_config(self, proto: IProtoSuite, test: ITestSuite):
        if not proto.is_distributed():
            proto_conf = proto.get_config()
            if proto_conf is None:
                logging.error("Protocol config is not set")
                return False
            hosts = proto_conf.hosts
            if hosts is None or len(hosts) != 2:
                logging.error(
                    "Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
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
