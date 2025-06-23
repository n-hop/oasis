from interfaces.routing import IRoutingStrategy


class StaticRouting(IRoutingStrategy):
    """Summary:
    Configure static routing for the chain network.
    """

    def __init__(self):
        self.pair_to_link_ip = {}
        self.net_routes = []

    def setup_routes(self, network: 'INetwork'):
        '''
        Setup the routing by ip route.
        '''
        hosts = network.get_hosts()
        self.pair_to_link_ip = network.get_link_table()
        self.net_routes = [range(network.get_num_of_host())]
        for route in self.net_routes:
            route = [hosts[i] for i in route]
            self._add_route(route)

    @staticmethod
    def _add_ip_gateway(host, gateway_ip, dst_ip):
        host.cmd(f'ip r a {dst_ip} via {gateway_ip}')

    def _add_route(self, route):
        for i in range(len(route) - 1):
            for j in range(i + 1, len(route)):
                host = route[i]
                gateway = route[i + 1]
                dst_prev = route[j - 1]
                dst = route[j]
                if j < len(route) - 1:
                    dst_next = route[j + 1]

                # gateway ip is the ip of the second (right) interface
                # of the link (route_i, route_{i+1})
                gateway_ip = self.pair_to_link_ip[(host, gateway)]

                # dst ip is the ip of the second (right) interface in the link
                # (route_{j-1}, route_j)
                dst_ip = self.pair_to_link_ip[(dst_prev, dst)]
                if j < len(route) - 1:
                    dst_ip_right = self.pair_to_link_ip[(dst_next, dst)]
                self._add_ip_gateway(host, gateway_ip, dst_ip)
                if j < len(route) - 1:
                    self._add_ip_gateway(host, gateway_ip, dst_ip_right)

        for i in range(1, len(route)):
            for j in range(0, i):
                host = route[i]
                gateway = route[i - 1]
                dst_prev = route[j + 1]
                dst = route[j]

                if j >= 1:
                    dst_next = route[j - 1]

                gateway_ip = self.pair_to_link_ip[(host, gateway)]
                dst_ip = self.pair_to_link_ip[(dst_prev, dst)]
                if j >= 1:
                    dst_ip_left = self.pair_to_link_ip[(dst_next, dst)]
                self._add_ip_gateway(host, gateway_ip, dst_ip)
                if j >= 1:
                    self._add_ip_gateway(host, gateway_ip, dst_ip_left)
