from interfaces.network_mgr import (INetworkManager, NetworkType)
from .network_mgr import NetworkManager


def create_network_mgr(type: NetworkType) -> INetworkManager:
    if type == NetworkType.containernet:
        return NetworkManager()
    return NetworkManager()
