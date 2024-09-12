from interfaces.network import INetwork
from protosuites.bats.bats_protocol import BATSProtocol


class BRTPProxy(BATSProtocol):
    """BATS protocol BRTP-proxy mode.
    # The Iperf3 default port 5201 is set to exclude_port on the ini, for TCP proxy we use 5202
    """

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        routing_type_name = network.get_routing_strategy().routing_type()
        if routing_type_name == 'OLSRRouting':
            host = network.get_hosts()[host_id]
            return self._get_ip_from_host(host, 'lo label lo:olsr')

        return ""
