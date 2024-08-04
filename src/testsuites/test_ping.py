
import logging

from interfaces.network import INetwork
from .test import (ITestSuite)


class PingTest(ITestSuite):
    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_test(self, network: INetwork):
        hosts = network.get_hosts()
        hosts_num = len(hosts)
        for i in range(hosts_num):
            if i == 0:
                continue
            logging.info(
                f"############### Oasis PingTest from "
                "%s to %s ###############",hosts[i].name(), hosts[0].name())
            res = hosts[i].cmd('ping -c 5 -W 1 -i 0.1 %s' % hosts[0].IP())
            logging.info('host %s', res)
            if "100% packet loss" in res:
                logging.error("Ping test failed")
                return False
        return True
