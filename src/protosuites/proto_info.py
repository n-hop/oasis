from abc import ABC, abstractmethod


class IProtoInfo(ABC):
    """For a classic proxy protocol, it should have defined at least one of the following IPC mechanisms:
    - UDP forward port
    - TUN interface
    - UDS listening port
    """
    @abstractmethod
    def get_forward_port(self) -> int:  # type: ignore
        """The UDP forward port of the protocol.
        """

    @abstractmethod
    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:  # type: ignore
        """The ip address of the tun interface on host `host_id`

        Returns:
            str: ip address of the tun interface
        """

    @abstractmethod
    def get_protocol_name(self) -> str:
        """The name of the protocol
        """

    def is_distributed(self) -> bool:
        return True

    def get_protocol_version(self) -> str:
        return None
