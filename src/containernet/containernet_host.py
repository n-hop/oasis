# adapter pattern
from interfaces.host import IHost

class ContainernetHostAdapter(IHost):
    def __init__(self, containernet_host):
        self.containernet_host = containernet_host

    def cmd(self, command):
        return self.containernet_host.cmd(command)

    def name(self) -> str:
        """Get the name of the host.
        """
        return self.containernet_host.name

    def IP(self) -> str:
        """Get the IP address of the host.
        """
        return self.containernet_host.IP()

    def deleteIntfs(self):
        """Delete all interfaces.
        """
        return self.containernet_host.deleteIntfs()

    def cleanup(self):
        """Cleanup the host.
        """
        return self.containernet_host.cleanup()

    def get_host(self):
        return self.containernet_host
    