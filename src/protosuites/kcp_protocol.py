import logging
from protosuites.proto import (ProtoConfig, IProtoSuite)
from interfaces.network import INetwork
from .proto_info import IProtoInfo


class KCPProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.path is None:
            logging.error("No protocol path specified.")
        self.process_name = self.config.path.split('/')[-1]
        self.forward_port = 5201

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
        hosts = network.get_hosts()
        conf_host = self.config.hosts
        if self.config.role == "client":
            id = conf_host[0]
            receiver_ip = hosts[conf_host[-1]].IP()
            args = f'-r {receiver_ip}:4000' + f' -l :{self.forward_port}' + \
                ' ' + self.config.args
            res = hosts[id].cmdPrint(f'{self.config.path} {args}'
                                     f' > {self.log_dir}kcp_protocol_h{id}.log &')
            logging.info(f"############### Oasis run kcp protocol on %s, %s ###############",
                         hosts[id].name(), res)
        elif self.config.role == "server":
            id = conf_host[-1]
            target_ip = hosts[id].IP()
            args = f'-t {target_ip}:{self.forward_port}' + \
                ' ' + self.config.args
            res = hosts[id].cmdPrint(f'{self.config.path} {args}'
                                     f' > {self.log_dir}kcp_protocol_h{id}.log &')
            logging.info(f"############### Oasis run kcp protocol on %s, %s ###############",
                         hosts[id].name(), res)
        else:
            logging.error("No role specified.")
            return False
        return True

    def stop(self, network: INetwork):
        hosts = network.get_hosts()
        host = None
        if self.config.role == "client":
            host = hosts[self.config.hosts[0]]
        elif self.config.role == "server":
            host = hosts[self.config.hosts[-1]]
        host.cmdPrint(f'pkill -f {self.process_name}')
        logging.info(
            f"############### Oasis stop kcp protocol on %s ###############", host.name())
        return True

    def get_forward_port(self) -> int:
        return self.forward_port

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return "KCP"

    def get_protocol_version(self) -> str:
        return self.config.version
