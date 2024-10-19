import logging

from containernet.config import NodeConfig
from containernet.containernet_network import ContainerizedNetwork
from containernet.topology import ITopology
from routing.routing_factory import RoutingFactory, route_string_to_enum

# alphabet table
alphabet = ['h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't']


class NetworkManager:
    """NetworkManager manages multiple network instances.
    """

    def __init__(self):
        self.networks = []
        self.num_of_networks = 0

    def get_top_description(self):
        if len(self.networks) > 0:
            return self.networks[0].get_topology_description()
        return ''

    def get_networks(self):
        return self.networks

    def build_networks(self, node_config: NodeConfig,
                       topology: ITopology,
                       num_networks: int,
                       route: str = "static_route"):
        """Build multiple network instances based on the given topology.

        Args:
            node_config (NodeConfig): The configuration of each node in the network.
            topology (ITopology): The topology to be built.
            num_networks (int): The number of networks to be built.
            route (str, optional): The route strategy. Defaults to "static_route".

        Returns:
            bool: True if the networks are built successfully, False otherwise.
        """
        if num_networks > len(alphabet):
            logging.error("Error: number of networks exceeds the limit.")
            return False
        org_name_prefix = node_config.name_prefix
        cur_net_num = len(self.networks)
        logging.info(
            "########## Oasis request network number %s.", num_networks)
        if cur_net_num < num_networks:
            for i in range(cur_net_num, num_networks):
                if num_networks > 1:
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
                self.networks.append(ContainerizedNetwork(
                    node_config, topology, route_strategy))
        elif cur_net_num > num_networks:
            # stop the extra networks
            for i in range(num_networks, cur_net_num):
                self.networks[i].stop()
                logging.info("########## Oasis stop the network %s.", i)
            self.networks = self.networks[:num_networks]
        self.num_of_networks = len(self.networks)
        return True

    def start_networks(self, top_config: ITopology):
        """reload networks if networks is already built; otherwise, start networks.

        Args:
            topology (ITopology): The topology to be built.
        """
        for i in range(self.num_of_networks):
            if not self.networks[i].is_started():
                self.networks[i].start()
            else:
                # reload the network instances can save time
                self.networks[i].reload(top_config)
            logging.info("########## Oasis start the network %s.", i)

    def stop_networks(self):
        # Stop all networks
        for i in range(self.num_of_networks):
            self.networks[i].stop()
            logging.info("########## Oasis stop the network %s.", i)

    def reset_networks(self):
        # Reset all networks
        for i in range(self.num_of_networks):
            self.networks[i].reset()
            logging.info("########## Oasis reset the network %s.", i)
