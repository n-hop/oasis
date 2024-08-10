import logging
from abc import ABC, abstractmethod
from containernet.topology import (ITopology)
from testsuites.test import ITestSuite
from protosuites.proto import IProtoSuite


class INetwork(ABC):
    def __init__(self):
        self.is_protocol_set = False
        self.test_suites = []
        self.protocol_instance = None

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
    def reload(self, top: ITopology):
        pass

    def init_protocol(self, proto_suite: IProtoSuite):
        self.protocol_instance = proto_suite
        self.protocol_instance.start(self)
        self.is_protocol_set = True

    def add_test_suite(self, test_suite: ITestSuite):
        self.test_suites.append(test_suite)

    def perform_test(self):
        if not self.is_protocol_set:
            logging.error("No protocol set")
            return False
        if self.test_suites is None:
            logging.error("No test suite set")
            return False
        for test in self.test_suites:
            test.run(self)
        return True

    def reset(self):
        self.protocol_instance.stop(self)
        self.test_suites = []
        self.is_protocol_set = False
        self.protocol_instance = None
