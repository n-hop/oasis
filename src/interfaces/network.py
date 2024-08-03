import logging
from abc import ABC, abstractmethod
from containernet.topology import (ITopology)
from testsuites.test import ITestSuite


class INetwork(ABC):
    def __init__(self):
        self.test_suites = []

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
    def reload(self, top: ITopology):
        pass

    def add_test_suite(self, test_suite: ITestSuite):
        self.test_suites.append(test_suite)

    def perform_test(self):
        if self.test_suites is None:
            logging.error("No test suite set")
        for test in self.test_suites:
            test.run(self)

    def reset_test_suites(self):
        self.test_suites = []
