from abc import ABC, abstractmethod
from enum import IntEnum


class RouteType(IntEnum):
    static = 0
    olsr = 1
    openr = 2
    static_bfs = 3


class IRoutingStrategy(ABC):
    @abstractmethod
    def setup_routes(self, network):
        pass

    def teardown_routes(self, network):
        pass

    def routing_type(self):
        return self.__class__.__name__
