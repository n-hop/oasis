from interfaces.network_mgr import (INetworkManager, NetworkType)
from .network_mgr import NetworkManager
from .testbed_mgr import TestbedManager


def create_network_mgr(type: NetworkType) -> INetworkManager:
    if type == NetworkType.containernet:
        return NetworkManager()
    if type == NetworkType.testbed:
        return TestbedManager()
    return NetworkManager()
