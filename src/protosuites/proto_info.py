from abc import ABC, abstractmethod


class IProtoInfo(ABC):
    """For a classic proxy protocol, it should have defined at least one of the following IPC mechanisms:
    - UDP forward port
    - TUN interface
    - UDS listening port
    """
    @abstractmethod
    def get_forward_port(self) -> int:
        """The UDP forward port of the protocol.
        """

    @abstractmethod
    def get_tun_ip(self) -> str:
        """The ip address of the tun interface.

        Returns:
            str: ip address of the tun interface
        """
