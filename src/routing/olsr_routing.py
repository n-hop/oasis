import logging
import time
from interfaces.routing import IRoutingStrategy
from var.global_var import g_root_path


class OLSRRouting(IRoutingStrategy):
    """Summary:
    Configure routing for the network with OLSR.
    """

    def __init__(self):
        self.binary_path = f"{g_root_path}bin/olsr/olsrd2_static"
        self.cfg_path = "/etc/olsr/olsr.config"

    def setup_routes(self, network: 'INetwork'):
        self.start(network)

    def teardown_routes(self, network: 'INetwork'):
        self.stop(network)

    def _generate_cfg(self, network: 'INetwork'):
        template = ""
        template += "[olsrv2]\n"
        template += "    originator  -127.0.0.1/8\n"
        template += "    originator  -::/0\n"
        template += "    originator  default_accept\n"
        template += "\n"
        template += "[interface]\n"
        template += "    hello_interval  1\n"
        template += "    hello_validity  20\n"
        template += "    bindto  -127.0.0.1/8\n"
        template += "    bindto  -::/0\n"
        template += "    bindto  default_accept\n"
        template += "\n"
        template += "[interface=lo]\n"
        template += "{interface}\n"
        # template += "[log]\n"
        # template += "         info          all\n"
        template += "\n"

        hosts = network.get_hosts()
        host_num = network.get_num_of_host()
        for i in range(host_num):
            interface = ""
            if i == 0:
                interface += f"[interface={hosts[i].name()}-eth0]\n\n"
                interface += "[lan_import=lan]\n"
                interface += "interface  eth0\n\n"
            elif i == host_num - 1:
                interface += f"[interface={hosts[i].name()}-eth0]\n\n"
            else:
                interface += f"[interface={hosts[i].name()}-eth0]\n"
                interface += f"[interface={hosts[i].name()}-eth1]\n\n"
            hosts[i].cmd(f'mkdir /etc/olsr')
            hosts[i].cmd(
                f'echo "{template.format(interface=interface)}" > {self.cfg_path}')
            hosts[i].cmd(
                f'ip addr add 172.23.1.{i + 1}/32 dev lo label \"lo:olsr\"')

    def start(self, network: 'INetwork'):
        self._generate_cfg(network)
        hosts = network.get_hosts()
        host_num = network.get_num_of_host()
        for host in hosts:
            host.cmd(f'nohup {self.binary_path} --load={self.cfg_path} &')
            # host.cmd(
            #     f'nohup {self.binary_path} --load={self.cfg_path} >
            #  {g_root_path}test_results/olsr{host.name()}.log &')
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
        logging.info(
            "OLSR routing is setup correctly at %u seconds.", wait_sec)
        return True

    def stop(self, network: 'INetwork'):
        hosts = network.get_hosts()
        for host in hosts:
            host.cmd(f'killall -9 {self.binary_path}')
        logging.info("OLSR routing is stopped.")
