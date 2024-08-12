from abc import ABC, abstractmethod


class IProtoInfo(ABC):
    @abstractmethod
    def get_forward_port(self) -> int:
        pass

    @abstractmethod
    def get_tun_ip(self) -> str:
        pass
