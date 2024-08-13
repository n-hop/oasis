import logging
from abc import ABC, abstractmethod
from containernet.topology import (ITopology)
from testsuites.test import ITestSuite
from protosuites.proto import IProtoSuite
from interfaces.routing import IRoutingStrategy


class INetwork(ABC):
    def __init__(self):
        self.test_suites = []
        self.proto_suites = []

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_hosts(self):
        pass

    @abstractmethod
    def get_num_of_host(self):
        pass

    @abstractmethod
    def get_host_ip_range(self):
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

    def add_protocol_suite(self, proto_suite: IProtoSuite):
        self.proto_suites.append(proto_suite)

    def add_test_suite(self, test_suite: ITestSuite):
        self.test_suites.append(test_suite)

    def perform_test(self):
        if self.proto_suites is None:
            logging.error("No protocol set")
            return False
        if self.test_suites is None:
            logging.error("No test suite set")
            return False
        # Combination of protocol and test
        for proto in self.proto_suites:
            # start the protocol
            proto.start(self)
            for test in self.test_suites:
                # run `test` on `network`(self) specified by `proto`
                test.run(self, proto)
            # stop the protocol
            proto.stop(self)
        return True

    def reset(self):
        self.proto_suites = []
        self.test_suites = []
