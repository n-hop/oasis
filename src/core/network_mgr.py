import logging

from core.config import NodeConfig
from core.topology import ITopology
from containernet.containernet_network import ContainerizedNetwork
from routing.routing_factory import RoutingFactory, route_string_to_enum
from interfaces.network_mgr import (INetworkManager, NetworkType)

# alphabet table
alphabet = ['h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't']


class NetworkManager(INetworkManager):
    """NetworkManager manages multiple network instances.
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

    def build_networks(self, node_config: NodeConfig,
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
        if net_num > len(alphabet):
            logging.error("Error: number of networks exceeds the limit.")
            return False
        org_name_prefix = node_config.name_prefix
        cur_net_num = len(self.networks)
        logging.info(
            "########## Oasis request network number %s.", net_num)
        if cur_net_num < net_num:
            for i in range(cur_net_num, net_num):
                if net_num > 1:
                    logging.info(
                        "####################################################")
                    logging.info(
                        "########## Oasis Parallel Execution Mode. ##########")
                    logging.info(
                        "########## network instance %s             ##########", i)
                    logging.info(
                        "####################################################")
                    node_config.name_prefix = f"{org_name_prefix}{alphabet[i]}"
                    node_config.bind_port = False
                route_strategy = RoutingFactory().create_routing(
                    route_string_to_enum[route])
                net = ContainerizedNetwork(
                    node_config, topology, route_strategy)
                net.id = i
                self.networks.append(net)
        elif cur_net_num > net_num:
            # stop the extra networks
            for i in range(net_num, cur_net_num):
                self.networks[i].stop()
                logging.info("########## Oasis stop the network %s.", i)
            self.networks = self.networks[:net_num]
        logging.info(
            "######################################################")
        logging.info("########## Oasis traverse the topologies: \n %s .",
                     self.get_top_description())
        logging.info(
            "######################################################")
        self.net_num = len(self.networks)
        # use `self.cur_top` to reload network
        self.cur_top = topology
        return True

    def start_networks(self):
        """reload networks if networks is already built; otherwise, start networks.
        """
        if self.cur_top is None:
            logging.error("Current topology is not set.")
        if self.net_num == 0:
            logging.error("nothing to start")
        for i in range(self.net_num):
            if not self.networks[i].is_started():
                self.networks[i].start()
                logging.info("########## Oasis start the network %s.", i)
            else:
                # reload the network instances can save time
                self.networks[i].reload(self.cur_top)
                logging.info("########## Oasis reload the network %s.", i)

    def stop_networks(self):
        # Stop all networks
        for i in range(self.net_num):
            self.networks[i].stop()
            logging.info("########## Oasis stop the network %s.", i)
        self.networks = []
        self.net_num = 0

    def reset_networks(self):
        # Reset all networks, mainly for routes/tc rules/ip config.
        for i in range(self.net_num):
            self.networks[i].reset()
            logging.info("########## Oasis reset the network %s.", i)
