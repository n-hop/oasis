import logging

from containernet.topology import ITopology
from interfaces.network_mgr import (INetworkManager, NetworkType)
from testbed.config import HostConfig


def load_all_hosts(testbed_yaml_config):
    hosts_config = []
    for host in testbed_yaml_config:
        host_config = HostConfig(**host)
        hosts_config.append(host_config)
        logging.info("loaded host_config: %s", host_config)
    if len(hosts_config) == 0:
        logging.error("No hosts are loaded for the testbed.")
        return None
    return False


class TestbedManager(INetworkManager):
    """TestbedManager manages multiple network instances.
    """

    def __init__(self):
        super().__init__()
        self.networks = []
        self.net_num = 0
        self.cur_top = None
        self.type = NetworkType.containernet

    def get_top_description(self):
        if len(self.networks) > 0:
            return self.networks[0].get_topology_description()
        return ''

    def get_networks(self):
        return self.networks

    def build_networks(self, node_config,
                       topology: ITopology,
                       net_num: int,
                       route: str = "static_route"):
        """Build multiple network instances based on the given topology.

        Args:
            node_config (NodeConfig): The configuration of each node in the network.
            topology (ITopology): The topology to be built.
            net_num (int): The number of networks to be built.
            route (str, optional): The route strategy. Defaults to "static_route".

        Returns:
            bool: True if the networks are built successfully, False otherwise.
        """
        logging.info("########## Oasis find access to testbed network.")
        all_hosts_conf = load_all_hosts(node_config)
        logging.info("########## The number of hosts: %s",
                     len(all_hosts_conf or []))
        return True

    def start_networks(self):
        logging.info("########## Oasis start access to testbed network.")

    def stop_networks(self):
        logging.info("########## Oasis stop access to testbed network.")

    def reset_networks(self):
        logging.info("########## Oasis reset access to testbed network.")
