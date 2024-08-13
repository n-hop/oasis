from protosuites.bats.bats_protocol import BATSProtocol
from interfaces.network import INetwork

class BRTP(BATSProtocol):
    """BATS protocol BRTP-TUN mode
    """

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        routing_type_name = network.get_routing_strategy().routing_type()
        if routing_type_name == 'StaticRouting':
            host = network.get_hosts()[host_id]
            return self._get_ip_from_host(host, 'tun_session')
        if routing_type_name == 'OLSRRouting':
            host = network.get_hosts()[host_id]
            return self._get_ip_from_host(host, 'olsr_tun_BRTP')
        return None
