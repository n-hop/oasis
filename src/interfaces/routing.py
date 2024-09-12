from abc import ABC, abstractmethod


class IRoutingStrategy(ABC):
    @abstractmethod
    def setup_routes(self, network):
        pass

    def teardown_routes(self, network):
        pass

    def routing_type(self):
        return self.__class__.__name__
