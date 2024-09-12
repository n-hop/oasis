import logging
from math import log
import time
from interfaces.routing import IRoutingStrategy


class OLSRRouting(IRoutingStrategy):
    """Summary:
    Configure routing for the network with OLSR.
    """

    def setup_routes(self, network: 'INetwork'):
        self.binary_path = "/root/bin/olsr/olsrd2_static"
        self.cfg_path = "/etc/olsr/olsr.config"
        self.start(network)

    def teardown_routes(self, network: 'INetwork'):
        self.stop(network)

    def _generate_cfg(self, network: 'INetwork'):
        self.template = ""
        self.template += "[olsrv2]\n"
        self.template += "    originator  -127.0.0.1/8\n"
        self.template += "    originator  -::/0\n"
        self.template += "    originator  default_accept\n"
        self.template += "\n"
        self.template += "[interface]\n"
        self.template += "    hello_interval  1\n"
        self.template += "    hello_validity  20\n"
        self.template += "    bindto  -127.0.0.1/8\n"
        self.template += "    bindto  -::/0\n"
        self.template += "    bindto  default_accept\n"
        self.template += "\n"
        self.template += "[interface=lo]\n"
        self.template += "{interface}\n"
        # self.template += "[log]\n"
        # self.template += "         info          all\n"
        self.template += "\n"

        hosts = network.get_hosts()
        host_num = network.get_num_of_host()
        for i in range(host_num):
            interface = ""
            if i == 0:
                interface += f"[interface=h{i}-eth0]\n\n"
                interface += "[lan_import=lan]\n"
                interface += "interface  eth0\n\n"
            elif i == host_num - 1:
                interface += f"[interface=h{i}-eth0]\n\n"
            else:
                interface += f"[interface=h{i}-eth0]\n"
                interface += f"[interface=h{i}-eth1]\n\n"
            hosts[i].cmd(f'mkdir /etc/olsr')
            hosts[i].cmd(
                f'echo "{self.template.format(interface=interface)}" > {self.cfg_path}')
            hosts[i].cmd(
                f'ip addr add 172.23.1.{i + 1}/32 dev lo label \"lo:olsr\"')

    def start(self, network: 'INetwork'):
        self._generate_cfg(network)
        hosts = network.get_hosts()
        host_num = network.get_num_of_host()
        for host in hosts:
            host.cmd(f'nohup {self.binary_path} --load={self.cfg_path} &')
            # host.cmd(
            #     f'nohup {self.binary_path} --load={self.cfg_path} > /root/test_results/olsr{host.name()}.log &')
        max_wait_sec = 20 + host_num * 3
        wait_sec = 0
        last_host_ip = f'172.23.1.{host_num}'
        while wait_sec < max_wait_sec:
            time.sleep(1)
            wait_sec += 1
            route = hosts[0].cmd(
                f'ip route | grep {last_host_ip} | grep -v grep')
            if route is not None and route.find(last_host_ip) != -1:
                break
        if wait_sec >= max_wait_sec:
            logging.error("OLSR routing is not setup correctly.")
            return False
        logging.info(f"OLSR routing is setup correctly at {wait_sec} seconds.")
        return True

    def stop(self, network: 'INetwork'):
        hosts = network.get_hosts()
        for host in hosts:
            host.cmd(f'killall -9 {self.binary_path}')
        logging.info("OLSR routing is stopped.")
