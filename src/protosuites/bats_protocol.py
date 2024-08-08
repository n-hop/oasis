import logging
from interfaces.network import INetwork
from tools.cfg_generator import generate_cfg_files
from .proto import IProtoSuite

class BATSProtocol(IProtoSuite):
    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        # Init the license file for bats, otherwise it will not run.
        hosts = network.get_hosts()
        if self.config.protocol_path is None or self.config.hosts is None:
            logging.error("No protocol path or hosts set")
            return False
        # get path from `self.config.protocol_path`
        prefix_path = '/'.join(self.config.protocol_path.split('/')[:-1])
        if prefix_path == '':
            prefix_path = '.'
        host_num = len(hosts)
        # prepare the bats protocol config files
        generate_cfg_files(host_num, network.node_ip_range, prefix_path)
        for i in range(host_num):
            hosts[i].cmd(
                f'mkdir -p /etc/cfg')
            hosts[i].cmd(
                f'cp {prefix_path}/licence /etc/cfg/')
            logging.info(
                f"############### Oasis install licence file on "
                "%s ###############",
                hosts[i].name())
            hosts[i].cmd(
                f'mkdir -p /etc/bats-protocol')
            hosts[i].cmd(f'mv {prefix_path}/h{i}.ini /etc/bats-protocol/bats-protocol-settings.ini')
            logging.info(
                f"############### Oasis install bats protocol config file on "
                "%s ###############",
                hosts[i].name())
        return True

    def run(self, network: INetwork):
        hosts = network.get_hosts()
        if self.config.protocol_path is None or self.config.hosts is None:
            logging.error("No protocol path or hosts set")
            return False
        host_num = len(hosts)
        for i in range(host_num):
            res = hosts[i].cmd(
                f'{self.config.protocol_path} {self.config.protocol_args} '
                f' ')
            logging.info(
                f"############### Oasis run bats protocol on "
                "%s, %s ###############",
                hosts[i].name(), res)
        return True

    def stop(self, network: INetwork):
        hosts = network.get_hosts()
        if self.config.protocol_path is None or self.config.hosts is None:
            logging.error("No protocol path or hosts set")
            return False
        process_name = self.config.protocol_path.split('/')[-1]
        host_num = len(hosts)
        for i in range(host_num):
            logging.info(
                f"############### Oasis stop bats protocol on "
                "%s ###############",
                hosts[i].name())
            hosts[i].cmd(
                f'pkill -f {process_name}')
        return True
