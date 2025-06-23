from interfaces.routing import (IRoutingStrategy, RouteType)
from routing.static_routing import StaticRouting
from routing.static_routing_bfs import StaticRoutingBfs
from routing.olsr_routing import OLSRRouting
from routing.openr_routing import OpenrRouting

# map string to type
route_string_to_enum = {
    'static_bfs': RouteType.static_bfs,
    'static_route': RouteType.static,
    'olsr_route': RouteType.olsr,
    'openr_route': RouteType.openr}


class RoutingFactory:
    def create_routing(self, routing_type: RouteType) -> IRoutingStrategy:
        if routing_type == RouteType.static:
            return StaticRouting()
        if routing_type == RouteType.static_bfs:
            return StaticRoutingBfs()
        if routing_type == RouteType.olsr:
            return OLSRRouting()
        if routing_type == RouteType.openr:
            return OpenrRouting()
        return None
