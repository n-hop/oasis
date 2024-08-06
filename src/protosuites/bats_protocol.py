import logging
from interfaces.network import INetwork
from .proto import IProtoSuite

class BATSProtocol(IProtoSuite):
    def post_run(self):
        return True

    def pre_run(self):
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
                f' > {self.config.log_file}')
            logging.info(
                f"############### Oasis run bats protocol on "
                "%s, %s ###############", 
                hosts[i].name(),res)
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
