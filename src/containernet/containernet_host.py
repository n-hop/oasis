import logging
from interfaces.host import IHost
from var.global_var import g_root_path


class ContainernetHostAdapter(IHost):
    def __init__(self, containernet_host):
        self.containernet_host = containernet_host
        self.__setup_ssh()

    def cmd(self, command):
        return self.containernet_host.cmd(command)

    def cmdPrint(self, command: str) -> str:
        """Execute a command on the host and print the output.
        """
        return self.containernet_host.cmdPrint(command)

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
        # clean up all tc qdisc rules.
        for intf in self.containernet_host.intfList():
            logging.debug(
                f"clean up tc qdisc on host %s, interface %s",
                self.containernet_host.name, intf.name)
            tc_output = self.containernet_host.cmd(
                f'tc qdisc show dev {intf.name}')
            if "priomap" not in tc_output and "noqueue" not in tc_output:
                self.containernet_host.cmd(
                    f'tc qdisc del dev {intf.name} root')
            intf_port = intf.name[-1]
            if intf_port.isdigit():
                ifb = f'ifb{intf_port}'
                tc_output = self.containernet_host.cmd(
                    f'tc qdisc show dev {ifb}')
                if "priomap" not in tc_output and "noqueue" not in tc_output:
                    self.containernet_host.cmd(
                        f'tc qdisc del dev {ifb} root')
        return self.containernet_host.cleanup()

    def get_host(self):
        return self.containernet_host

    def popen(self, command):
        return self.containernet_host.popen(command)

    def __setup_ssh(self):
        self.containernet_host.cmd("rm -rf /root/.ssh/")
        self.containernet_host.cmd("mkdir /root/.ssh/")
        self.containernet_host.cmdPrint(
            f'cp {g_root_path}src/config/keys/* /root/.ssh/')
        self.containernet_host.cmdPrint(
            "cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys")
        self.containernet_host.cmdPrint(
            "echo 'PermitRootLogin yes' | tee -a /etc/ssh/sshd_config")
        self.containernet_host.cmdPrint(
            "echo 'PasswordAuthentication no' | tee -a /etc/ssh/sshd_config")
        self.containernet_host.cmdPrint(
            "echo 'StrictModes no' | tee -a /etc/ssh/sshd_config")
        self.containernet_host.cmdPrint("service ssh start")
