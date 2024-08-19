import logging
from protosuites.proto import (ProtoConfig, IProtoSuite)
from interfaces.network import INetwork
from .proto_info import IProtoInfo

class KCPProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config:ProtoConfig):
        super().__init__(config)

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork, client_host:int, server_host:int):
        hosts = network.get_hosts()
        args = ""
        if self.config.protocol_args == "client":
            recver_ip = hosts[-1].IP()
            if server_host != None:
                recver_ip = hosts[server_host].IP()
            args = (f'-r {recver_ip}:4000'
                    f' -l :5201'
                    f' -mode fast3 --datashard 10 --parityshard 3'
                    f' -nocomp'
                    f' -autoexpire 900'
                    f' -sockbuf 16777217'
                    f' -dscp 46 '
                    f' --crypt=none'
            )
            client_host = client_host if client_host != None else 0
            res = hosts[client_host].cmdPrint(f'nohup {self.config.protocol_path} {args}'
                                              f' > kcp_protocol_client.log &')
            logging.info(f"############### Oasis run kcp protocol on %s, %s ###############",
                            hosts[client_host].name(), res)
        else:
            server_host = server_host if server_host != None else len(hosts) - 1
            args = (f'-t {hosts[server_host].IP()}:5201'
                    f' -l :4000'
                    f' -mode fast3 --datashard 10 --parityshard 3'
                    f' -nocomp'
                    f' -sockbuf 16777217'
                    f' -dscp 46'
                    f' --crypt=none'
            )
            res = hosts[server_host].cmdPrint(f'nohup {self.config.protocol_path} {args}'
                                              f' > kcp_protocol_server.log &')
            logging.info(f"############### Oasis run kcp protocol on %s, %s ###############",
                            hosts[server_host].name(), res)
        return True

    def stop(self, network: INetwork):
        hosts = network.get_hosts()
        for host in hosts:
            res = host.cmdPrint(f'pkill -f {self.config.protocol_path}')
        logging.info(f"############### Oasis stop kcp protocol ###############")
        return True

    def get_forward_port(self, network: 'INetwork', host_id: int) -> int:
        pass

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return "KCP"
