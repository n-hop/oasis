from abc import ABC, abstractmethod


class IHost(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def cmd(self, command: str) -> str:
        """Execute a command on the host.
        """

    def cmdPrint(self, command: str) -> str:
        """Execute a command on the host and print the output.
        """

    def popen(self, command: str):
        """Execute a command on the host using popen.
        """

    def name(self) -> str:
        """Get the name of the host.
        """
        return ""

    def IP(self) -> str:
        """Get the IP address of the host.
        """
        return ""

    def deleteIntfs(self):
        """Delete all interfaces.
        """

    def cleanup(self):
        """Cleanup the host.
        """

    def get_host(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the host is connected to the network.
            """
