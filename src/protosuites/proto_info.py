from abc import ABC, abstractmethod


class IProtoInfo(ABC):
    """For a classic proxy protocol, it should have defined at least one of the following IPC mechanisms:
    - UDP forward port
    - TUN interface
    - UDS listening port
    """
    @abstractmethod
    def get_forward_port(self, network: 'INetwork', host_id: int) -> int:  # type: ignore
        """The UDP forward port of the protocol on host `host_id`
        """

    @abstractmethod
    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:  # type: ignore
        """The ip address of the tun interface on host `host_id`

        Returns:
            str: ip address of the tun interface
        """
