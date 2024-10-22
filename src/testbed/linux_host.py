import logging
import subprocess
import os

from interfaces.host import IHost
from var.global_var import g_root_path
from .config import HostConfig


class LinuxHost(IHost):
    """Linux host class.

       Define the way to interact with a Linux host.
    """

    def __init__(self, config: HostConfig):
        self.host_config = config
        if self.host_config.ip is None:
            raise ValueError("The host IP is None.")
        if self.host_config.user is None:
            raise ValueError("The host user is None.")
        private_key = f"{g_root_path}{self.host_config.authorized_key}"
        # check if the private key exists.
        if not os.path.exists(private_key):
            raise FileNotFoundError(
                f"The private key {private_key} does not exist.")
        self.ssh_cmd_prefix = f"ssh -i {self.host_config.authorized_key} {self.host_config.user}@{self.host_config.ip}"
        self.intf_list = ['eth0', 'eth1']
        result = subprocess.run(
            [f"{self.ssh_cmd_prefix} hostname"], shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            self.is_connected_flag = True
            logging.info("Connected to the host %s", self.host_config.ip)
        else:
            logging.error("Failed to connect to the host %s: %s",
                          self.host_config.ip, result.stderr)
            self.is_connected_flag = False

    def is_connected(self) -> bool:
        return self.is_connected_flag

    def cmd(self, command):
        cmd_str = f"{self.ssh_cmd_prefix} \"{command}\""
        result = subprocess.run(
            [cmd_str], shell=True, capture_output=True, text=True, check=False)
        logging.debug("STDOUT: %s", result.stdout)
        logging.debug("STDERR: %s", result.stderr)
        if result.returncode != 0:
            logging.error("Command failed with return code %d: %s",
                          result.returncode, result.stderr)
        return result.stdout

    def cmdPrint(self, command: str) -> str:
        """Execute a command on the host and print the output.
        """
        logging.info(f"cmdPrint: %s", command)
        return self.cmd(command)

    def name(self) -> str:
        """Get the name of the host.
        """
        cmd_str = f"{self.ssh_cmd_prefix} hostname"
        return self.cmd(cmd_str)

    def IP(self) -> str:
        """Get the IP address of the host.
        """
        return self.host_config.ip

    def deleteIntfs(self):
        """Delete all interfaces.
        Action is not permitted.
        """
        return True

    def cleanup(self):
        """Cleanup the host.
        """
        # clean up all tc qdisc rules.
        for intf in self.intf_list:
            # src/tools/tc_rules.sh
            self.cmd(f"{g_root_path}src/tools/tc_rules.sh {intf} unset")

    def get_host(self):
        return self

    def popen(self, command):
        return self.cmd(command)
