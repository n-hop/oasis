import logging

from containernet.network import Network
from .test import (ITestSuite, TestType)


class IperfTest(ITestSuite):
    def __init__(self, type: TestType) -> None:
        super().__init__()
        self.type = type

    def post_process(self):
        pass

    def pre_process(self):
        pass

    def _run_test(self, network: Network):
        logging.info(
            "############### Oasis IperfTest ###########")
