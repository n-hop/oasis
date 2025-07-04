import logging
from interfaces.network import INetwork
from protosuites.proto import (ProtoConfig, IProtoSuite, ProtoRole)


class CSProtocol(IProtoSuite):
    def __init__(self, config: ProtoConfig, client: IProtoSuite, server: IProtoSuite):
        super().__init__(config, False, ProtoRole.both)
        self.client = client
        self.server = server
        if self.config.hosts is None or len(self.config.hosts) != 2:
            logging.error(
                "Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
            return
        self.client.get_config().hosts = [self.config.hosts[0]]
        self.server.get_config().hosts = [self.config.hosts[1]]
        # rewrite the protocol_args of client and server
        self.client.protocol_args += self.protocol_args
        self.server.protocol_args += self.protocol_args
        logging.info("CSProtocol config %s",
                     self.config)
        logging.info("client protocol %s args: %s",
                     self.client.config.name, self.client.protocol_args)
        logging.info("server protocol %s args: %s",
                     self.server.config.name, self.server.protocol_args)

    def is_distributed(self) -> bool:
        return False

    def is_noop(self) -> bool:
        return self.client.is_noop() and self.server.is_noop()

    def post_run(self, network: INetwork):
        return self.client.post_run(network) and self.server.post_run(network)

    def pre_run(self, network: INetwork):
        if self.client.pre_run(network):
            return self.server.pre_run(network)
        return False

    def run(self, network: INetwork):
        return self.client.run(network) \
            and self.server.run(network)

    def stop(self, network: INetwork):
        return self.client.stop(network) and self.server.stop(network)

    def get_forward_port(self) -> int:
        return self.client.get_forward_port()

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        return self.client.get_tun_ip(network, host_id)

    def get_protocol_name(self) -> str:
        return self.config.name

    def get_protocol_args(self, network: INetwork) -> str:
        return self.protocol_args
