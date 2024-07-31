import logging
import os
from mininet.net import Containernet
from mininet.util import ipStr, netParse
from mininet.link import TCLink
from containernet.topology import (ITopology, MatrixType)
from containernet.test_suites.test import ITestSuite
from .config import NodeConfig


def subnets(base_ip, parent_ip):
    """
    Find all the sibling subnets of `base_ip` that lives in `parent_ip`
    """
    parent, parent_prefix_len = netParse(parent_ip)
    base, prefix_len = netParse(base_ip)

    max_ip = (0xffffffff >> parent_prefix_len) | parent
    step = 1 << 32 - prefix_len
    # not allowing x.255.255
    yield from range(base, max_ip, step)


class Network (Containernet):
    """
    Create a network from an adjacency matrix.
    """

    def __init__(self,
                 node_config: NodeConfig = None,
                 net_topology: ITopology = None,
                 ** params) -> None:
        super().__init__(**params)
        # NodeConfig: Docker node related
        self.node_img = node_config.node_img
        self.node_vols = node_config.node_vols
        self.node_bind_port = node_config.node_bind_port
        self.node_name_prefix = node_config.node_name_prefix
        self.node_ip_range = node_config.node_ip_range
        self.node_route = node_config.node_route
        self.topology_type = net_topology.get_topology_type()
        # `node_ip_start` init from node_ip_range
        base, _ = netParse(self.node_ip_range)
        self.node_ip_prefix = 24
        self.node_ip_start = ipStr(base) + f'/{self.node_ip_prefix}'
        # Topology related
        self.net_mat = net_topology.get_matrix(MatrixType.ADJACENCY_MATRIX)
        if self.net_mat is not None:
            self.num_of_hosts = len(self.net_mat)
        else:
            raise ValueError('The topology matrix is None.')
        self.net_loss_mat = net_topology.get_matrix(
            MatrixType.LOSS_MATRIX)
        self.net_bw_mat = net_topology.get_matrix(
            MatrixType.BANDW_MATRIX)
        self.net_latency_mat = net_topology.get_matrix(
            MatrixType.LATENCY_MATRIX)
        self.net_jitter_mat = net_topology.get_matrix(
            MatrixType.JITTER_MATRIX)
        self._check_node_vols()
        logging.info('self.node_vols %s', self.node_vols)
        logging.info('self.net_mat %s', self.net_mat)
        logging.info('self.net_loss_mat %s', self.net_loss_mat)
        logging.info('self.net_bw_mat %s', self.net_bw_mat)
        logging.info('self.net_latency_mat %s', self.net_latency_mat)
        logging.info('self.net_jitter_mat %s', self.net_jitter_mat)
        self.net_routes = [range(self.num_of_hosts)]
        self.pair_to_link = {}
        self.pair_to_link_ip = {}
        self.test_suites = []
        self._init_containernet()

    def get_hosts(self):
        return self.hosts

    def add_test_suite(self, test_suite: ITestSuite):
        self.test_suites.append(test_suite)

    def perform_test(self):
        if self.test_suites is None:
            logging.error("No test suite set")
        for test in self.test_suites:
            test.run(self)

    def reload(self, node_config: NodeConfig, top: ITopology):
        """
        Reload the network with new configurations.
        """
        # check topology change only.
        if self.net_mat != top.get_matrix(MatrixType.ADJACENCY_MATRIX)\
           or self.net_loss_mat != top.get_matrix(MatrixType.LOSS_MATRIX)\
           or self.net_bw_mat != top.get_matrix(MatrixType.BANDW_MATRIX)\
           or self.net_latency_mat != top.get_matrix(MatrixType.LATENCY_MATRIX)\
           or self.net_jitter_mat != top.get_matrix(MatrixType.JITTER_MATRIX):
            self.net_mat = top.get_matrix(MatrixType.ADJACENCY_MATRIX)
            self.net_loss_mat = top.get_matrix(MatrixType.LOSS_MATRIX)
            self.net_bw_mat = top.get_matrix(MatrixType.BANDW_MATRIX)
            self.net_latency_mat = top.get_matrix(MatrixType.LATENCY_MATRIX)
            self.net_jitter_mat = top.get_matrix(MatrixType.JITTER_MATRIX)
            diff = self.num_of_hosts - len(self.net_mat)
            if diff < 0:
                self._expand_network(-diff, node_config)
            else:
                self._shrink_network(diff, node_config)

    def _init_containernet(self):
        self._setup_docker_nodes()
        self._setup_topology()
        self._setup_routes()

    def _setup_docker_nodes(self):
        """
        Setup the docker nodes related configurations,
        such as image, volume, and port binding.
        """
        for i in range(self.num_of_hosts):
            if self.node_bind_port:
                port_bindings = {i + 10000: i + 10000}
                ports = [i + 10000]
            else:
                port_bindings = {}
                ports = []
            self.addDocker(
                f'{self.node_name_prefix}{i}',
                ip=None,
                volumes=self.node_vols,
                cap_add=["NET_ADMIN", "SYS_ADMIN"],
                dimage=self.node_img,
                ports=ports,
                port_bindings=port_bindings,
                publish_all_ports=True
            )
        logging.info(
            "setup_docker_nodes, num. of nodes is %s.", self.num_of_hosts)
        return True

    def _setup_topology(self):
        """
        Setup the topology of the network by adding routes, links, etc.
        """
        link_subnets = subnets(self.node_ip_start, self.node_ip_range)
        _, link_prefix = netParse(self.node_ip_start)
        # for adjacent matrix, only the upper triangle is used.
        logging.info("num_of_hosts: %s", self.num_of_hosts)
        for i in range(self.num_of_hosts):
            for j in range(i, self.num_of_hosts):
                if self.net_mat[i][j] == 1:
                    link_ip = next(link_subnets)
                    left_ip = ipStr(link_ip + 1) + f'/{link_prefix}'
                    right_ip = ipStr(link_ip + 2) + f'/{link_prefix}'
                    logging.info(
                        "addLink: %s(%s) <--> %s(%s)",
                        self.hosts[i].name,
                        left_ip,
                        self.hosts[j].name,
                        right_ip
                    )
                    self.__addLink(i, j,
                                   params1={'ip': left_ip},
                                   params2={'ip': right_ip}
                                   )
                    self.pair_to_link_ip[(
                        self.hosts[i], self.hosts[j])] = ipStr(link_ip + 2)
                    self.pair_to_link_ip[(
                        self.hosts[j], self.hosts[i])] = ipStr(link_ip + 1)
        for host in self.hosts:
            host.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
            host.cmd('sysctl -p')
        logging.info(
            "############### Oasis Init Networking done ###########")
        return True

    def __addLink(
            self,
            id1,
            id2,
            port1=None,  # used to attach the interface to a switch.
            port2=None,  # used to attach the interface to a switch.
            **params):
        ''' Set link parameters
        # Link with TC interfaces
        # net.addLink(s1, s2, cls=TCLink, \
            delay = "100ms", bw = 1, loss = 10, jitter = 5)
        # FIXME: Warning: sch_htb: quantum of \
            class 50001 is big. Consider r2q change.
        '''
        if self.net_bw_mat is not None:
            params['bw'] = self.net_bw_mat[id1][id2]
        if self.net_loss_mat is not None:
            params['loss'] = self.net_loss_mat[id1][id2]
        if self.net_latency_mat is not None:
            params['delay'] = str(self.net_latency_mat[id1][id2]) + 'ms'
        if self.net_jitter_mat is not None:
            params['jitter'] = self.net_jitter_mat[id1][id2]
        link = super().addLink(
            self.hosts[id1], self.hosts[id2],
            port1, port2, cls=TCLink, **params)
        return link

    def _setup_routes(self):
        if self.node_route == 'ip' and self.topology_type != 'linear':
            logging.error(
                "The ip routing config %s is not supported for %s.",
                self.node_route, self.topology_type)
        # setup routes
        if self.node_route == 'ip':
            self._setup_ip_routes()
        elif self.node_route == 'olsr':
            self._setup_olsr_routes()
        else:
            logging.error(
                "The routing config %s is not supported.", self.node_route)

    def _setup_ip_routes(self):
        '''
        Setup the routing by ip route.
        '''
        for route in self.net_routes:
            route = [self.nameToNode[f'h{i}'] for i in route]
            self._add_route(route)

    def _setup_olsr_routes(self):
        '''
        setup the OLSR routing
        '''

    @ staticmethod
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

    def _check_node_vols(self):
        if not os.path.exists('/usr/bin/perf') or \
                not os.path.isfile('/usr/bin/perf'):
            logging.warning("perf is not available.")
            self.node_vols = [
                vol for vol in self.node_vols if '/usr/bin/perf' not in vol]

    def _expand_network(self, diff, node_config):
        """
        Expand the network by adding more nodes.
        """
        logging.info(
            "Reload the network. number of "
            "nodes increased by %s, node %s",
            diff, node_config)
        self._reset_network(self.num_of_hosts, diff)
        for i in range(diff):
            self.addDocker(
                f'{self.node_name_prefix}{self.num_of_hosts + i}',
                ip=None,
                volumes=node_config.node_vols,
                cap_add=["NET_ADMIN", "SYS_ADMIN"],
                dimage=node_config.node_img,
                ports=[self.num_of_hosts + i + 10000],
                port_bindings={self.num_of_hosts + i +
                               10000: self.num_of_hosts + i + 10000},
                publish_all_ports=True
            )
        self.num_of_hosts += diff
        self._setup_topology()
        self._setup_routes()
        logging.info(
            "Expand the network. number of nodes increased by %s, node %s",
            diff, node_config)
        return True

    def _shrink_network(self, diff, node_config):
        logging.info(
            "Reload the network. number of "
            "nodes decreased by %s, node %s",
            diff, node_config)
        self._reset_network(self.num_of_hosts, -diff)
        for i in range(self.num_of_hosts - diff, self.num_of_hosts):
            logging.info("removeDocker: %s", f'{self.node_name_prefix}{i}')
            self.removeDocker(f'{self.node_name_prefix}{i}')
        self.num_of_hosts -= diff
        self._setup_topology()
        self._setup_routes()
        return True

    def _reset_network(self, num, diff):
        logging.info("Reset the network.")
        # remove all links
        for i in range(num - 1):
            logging.info("removeLink: %s-%s",
                         self.hosts[i].name, self.hosts[i+1].name)
            self.removeLink(
                node1=self.hosts[i].name, node2=self.hosts[i+1].name)
        # remove all routes.
        for host in self.hosts:
            host.cmd('ip route flush table main')
            host.deleteIntfs()
            host.cleanup()
        self.net_routes = [range(self.num_of_hosts + diff)]
        self.pair_to_link = {}
        self.pair_to_link_ip = {}
        return True
