import logging
from abc import ABC, abstractmethod
from containernet.topology import (ITopology)
from testsuites.test import (ITestSuite, TestType)
from protosuites.proto import IProtoSuite
from interfaces.routing import IRoutingStrategy
from data_analyzer.analyzer import AnalyzerConfig
from data_analyzer.analyzer_factory import AnalyzerFactory


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
        """Perform the test for each input case from YAML file
        """
        if self.proto_suites is None:
            logging.error("No protocol set")
            return False
        if self.test_suites is None:
            logging.error("No test suite set")
            return False
        # Combination of protocol and test
        test_results = {}
        for proto in self.proto_suites:
            for test in self.test_suites:
                # start the protocol
                proto.start(self, test.config.client_host, test.config.server_host)
                # run `test` on `network`(self) specified by `proto`
                test.run(self, proto)
                if test.type() not in test_results:
                    test_results[test.type()] = []
                test_results[test.type()].append(test.log_file())
                # stop the protocol
                proto.stop(self)
        # Analyze the test results
        for test_type, log_files in test_results.items():
            # analyze the test results
            if test_type == TestType.throughput:
                config = AnalyzerConfig(
                    input=log_files, output="iperf3_throughput.svg")
                analyzer = AnalyzerFactory.get_analyzer("iperf3", config)
                analyzer.analyze()
                analyzer.visualize()
                logging.info(
                    "Analyzed and visualized the throughput test results")
        return True

    def reset(self):
        self.proto_suites = []
        self.test_suites = []
