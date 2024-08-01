import logging

from containernet.topology import (ITopology)
from interfaces.network import INetwork


class TestbedNetwork (INetwork):
    """
    Testbed is the network of fixed topology.
    """

    def __init__(self,
                 ** params) -> None:
        super().__init__(**params)
        self.num_of_hosts = 6
        self.net_routes = [range(self.num_of_hosts)]
        self.pair_to_link = {}
        self.pair_to_link_ip = {}
        self.test_suites = []

    def get_hosts(self):
        pass

    def start(self):
        logging.info("Oasis starts the TestbedNetwork.")

    def stop(self):
        logging.info("Oasis stop the TestbedNetwork.")

    def reload(self, top: ITopology):
        """
        Reload the network with new configurations.
        """
