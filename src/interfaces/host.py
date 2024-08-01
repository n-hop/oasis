from abc import ABC, abstractmethod


class IHost(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def cmd(self, input: str) -> str:
        """Execute a command on the host.
        """
