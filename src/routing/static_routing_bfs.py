
import logging
from collections import deque
from interfaces.routing import IRoutingStrategy


class StaticRoutingBfs(IRoutingStrategy):
    """Summary:
    Configure static routing for the network using BFS to find the shortest path.
    StaticRoutingBfs is the replacement for StaticRouting which only works with the chain network.
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
        adjacency = network.net_mat  # adjacency matrix
        num_hosts = len(hosts)

        # Compute next hops for all pairs using BFS
        for src in range(num_hosts):
            for dst in range(num_hosts):
                if src == dst:
                    continue
                path = self._bfs_shortest_path(adjacency, src, dst)
                if not path or len(path) < 2:
                    # No path or already at destination
                    continue
                next_hop = path[1]
                # Find the IP of the next hop interface
                gateway_ip = self.pair_to_link_ip.get(
                    (hosts[src], hosts[next_hop]))
                dst_ip = hosts[dst].IP()
                if gateway_ip:
                    self._add_ip_gateway(hosts[src], gateway_ip, dst_ip)
                    logging.debug(
                        "Static route: %s -> %s via %s (%s)",
                        hosts[src].name(), hosts[dst].name(), hosts[next_hop].name(), gateway_ip)
                else:
                    logging.warning(
                        f"No link IP for %s to %s", hosts[src].name(), hosts[next_hop].name())

    @staticmethod
    def _add_ip_gateway(host, gateway_ip, dst_ip):
        host.cmd(f'ip r a {dst_ip}/32 via {gateway_ip}')

    def _bfs_shortest_path(self, adjacency, start, goal):
        queue = deque([[start]])
        visited = set()
        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == goal:
                return path
            if node in visited:
                continue
            visited.add(node)
            for neighbor, connected in enumerate(adjacency[node]):
                if connected and neighbor not in visited:
                    queue.append(path + [neighbor])
        return None
