from interfaces.host import IHost


class TestbedHost(IHost):

    def cmd(self, input: str) -> str:
        """Execute a command on the host.
        """
