from abc import ABC, abstractmethod
from enum import IntEnum
from containernet.topology import ITopology

# alphabet table
alphabet = ['h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't']


class NetworkType(IntEnum):
    containernet = 0      # networks constructed by `containernet`
    testbed = 1  # networks constructed by real devices
    none = 2


class INetworkManager(ABC):
    """NetworkManager manages multiple network instances.
    """

    def __init__(self):
        self.networks = []
        self.net_num = 0
        self.cur_top = None
        self.type = NetworkType.none

    def get_type(self):
        return self.type

    def get_networks(self):
        return self.networks

    @abstractmethod
    def get_top_description(self):
        pass

    @abstractmethod
    def build_networks(self, node_config,
                       topology: ITopology,
                       net_num: int,
                       route: str = "static_route"):
        pass

    @abstractmethod
    def start_networks(self):
        pass

    @abstractmethod
    def stop_networks(self):
        pass

    @abstractmethod
    def reset_networks(self):
        pass
