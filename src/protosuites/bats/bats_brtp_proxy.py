from interfaces.network import INetwork
from protosuites.bats.bats_protocol import BATSProtocol


class BRTPProxy(BATSProtocol):
    """BATS protocol BRTP-proxy mode.
    """

    def get_forward_port(self) -> int:
        # The Iperf3 default port 5201 is set to exclude_port on the ini, for TCP proxy we use 5202
        return 5202

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return 'BRTP_PROXY'
