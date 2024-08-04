from interfaces.host import IHost


class TestbedHost(IHost):

    def cmd(self, command: str) -> str:
        """Execute a command on the host.
        """

    def get_host(self):
        return self
