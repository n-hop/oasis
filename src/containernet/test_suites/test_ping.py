
import logging

from containernet.network import Network
from .test import (ITestSuite, TestType)


class PingTest(ITestSuite):
    def __init__(self, type: TestType) -> None:
        super().__init__()
        self.type = type

    def post_process(self):
        pass

    def pre_process(self):
        pass

    def _run_test(self, network: Network):
        logging.info(
            "############### Oasis PingTest ###########")
        hosts = network.get_hosts()
        for host in hosts:
            res = host.cmd('ping -c 5 -W 1 -i 0.1 %s' % hosts[0].IP())
            logging.info('host %s', res)
