
import logging

from interfaces.network import INetwork
from .test import (ITestSuite)


class PingTest(ITestSuite):
    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_test(self, network: INetwork):
        logging.info(
            "############### Oasis PingTest ###########")
        hosts = network.get_hosts()
        for host in hosts:
            res = host.cmd('ping -c 5 -W 1 -i 0.1 %s' % hosts[0].IP())
            logging.info('host %s', res)
