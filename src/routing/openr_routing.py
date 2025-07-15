from interfaces.routing import IRoutingStrategy

class OpenrRouting(IRoutingStrategy):
    """Summary:
    Configure routing for the network with open-r.
    """
    def setup_routes(self, network: 'INetwork'):  # type: ignore
        pass
