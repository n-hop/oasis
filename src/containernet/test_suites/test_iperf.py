import logging

from containernet.network import Network
from containernet.data_analyzer.analyzer import AnalyzerConfig
from containernet.data_analyzer.analyzer_factory import AnalyzerFactory
from .test import (ITestSuite, TestType)


class IperfTest(ITestSuite):
    def __init__(self, type: TestType) -> None:
        super().__init__()
        self.type = type

    def post_process(self):
        analyzer = AnalyzerFactory.get_analyzer("iperf3")
        config = AnalyzerConfig()
        config.input = self.log_file
        config.output = "iperf3_result.svg"
        analyzer.analyze(config)
        analyzer.visualize(config)

    def pre_process(self):
        self.log_file = "iperf3_log.txt"

    def _run_test(self, network: Network):
        logging.info(
            "############### Oasis IperfTest ###########")
