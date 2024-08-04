from abc import ABC, abstractmethod

class IRoutingStrategy(ABC):
    @abstractmethod
    def setup_routes(self, network):
        pass
