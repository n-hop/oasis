from interfaces.routing import IRoutingStrategy

class OLSRRouting(IRoutingStrategy):
    """Summary:
    Configure routing for the network with OLSR.
    """
    def setup_routes(self, network: 'INetwork'):  # type: ignore
        pass
        