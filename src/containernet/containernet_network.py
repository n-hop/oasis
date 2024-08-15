import logging
import os
from mininet.net import Containernet
from mininet.util import ipStr, netParse
from mininet.link import TCLink
from containernet.topology import (ITopology, MatrixType)
from containernet.containernet_host import ContainernetHostAdapter
from interfaces.network import INetwork
from interfaces.routing import IRoutingStrategy
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


class ContainerizedNetwork (INetwork):
    """
    Create a network from an adjacency matrix.
    """

    def __init__(self,
                 node_config: NodeConfig = None,
                 net_topology: ITopology = None,
                 routing_strategy: IRoutingStrategy = None,
                 ** params) -> None:
        super().__init__(**params)
        self.containernet = Containernet()
        self.routing_strategy = routing_strategy
        self.hosts = []
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
        self._init_matrix(net_topology)
        self._check_node_vols()
        logging.info('self.node_vols %s', self.node_vols)
        if self.net_mat is not None:
            self.num_of_hosts = len(self.net_mat)
        else:
            raise ValueError('The topology matrix is None.')
        self.net_routes = [range(self.num_of_hosts)]
        self.pair_to_link = {}
        self.pair_to_link_ip = {}
        self.test_suites = []
        self._init_containernet()

    def get_hosts(self):
        return self.hosts

    def get_num_of_host(self):
        return self.num_of_hosts

    def get_host_ip_range(self):
        return self.node_ip_range

    def get_routing_strategy(self):
        return self.routing_strategy

    def start(self):
        logging.info("Oasis starts the ContainerizedNetwork.")
        self.containernet.build()
        self.containernet.start()

    def stop(self):
        self.containernet.stop()

    def reload(self, top: ITopology):
        """
        Reload the network with new configurations.
        """
        # check topology change only.
        if self._check_topology_change(top):
            self._init_matrix(top)
            diff = self.num_of_hosts - len(self.net_mat)
            if diff < 0:
                self._expand_network(-diff)
            else:
                self._shrink_network(diff)

    def get_link_table(self):
        return self.pair_to_link_ip

    def _check_topology_change(self, top: ITopology):
        is_changed = False
        if self.net_mat != top.get_matrix(MatrixType.ADJACENCY_MATRIX):
            is_changed = True
            logging.info("Oasis detected the topology change.")
        if self.net_loss_mat != top.get_matrix(MatrixType.LOSS_MATRIX):
            is_changed = True
            logging.info("Oasis detected the loss matrix change.")
        if self.net_bw_mat != top.get_matrix(MatrixType.BANDW_MATRIX):
            is_changed = True
            logging.info("Oasis detected the bandwidth matrix change.")
        if self.net_latency_mat != top.get_matrix(MatrixType.LATENCY_MATRIX):
            is_changed = True
            logging.info("Oasis detected the latency matrix change.")
        if self.net_jitter_mat != top.get_matrix(MatrixType.JITTER_MATRIX):
            is_changed = True
            logging.info("Oasis detected the jitter matrix change.")
        return is_changed

    def _init_matrix(self, net_topology: ITopology):
        self.net_mat = net_topology.get_matrix(MatrixType.ADJACENCY_MATRIX)
        self.net_loss_mat = net_topology.get_matrix(
            MatrixType.LOSS_MATRIX)
        self.net_bw_mat = net_topology.get_matrix(
            MatrixType.BANDW_MATRIX)
        self.net_latency_mat = net_topology.get_matrix(
            MatrixType.LATENCY_MATRIX)
        self.net_jitter_mat = net_topology.get_matrix(
            MatrixType.JITTER_MATRIX)
        logging.info('self.net_mat %s', self.net_mat)
        logging.info('self.net_loss_mat %s', self.net_loss_mat)
        logging.info('self.net_bw_mat %s', self.net_bw_mat)
        logging.info('self.net_latency_mat %s', self.net_latency_mat)
        logging.info('self.net_jitter_mat %s', self.net_jitter_mat)

    def _init_containernet(self):
        self._setup_docker_nodes(0, self.num_of_hosts - 1)
        self._setup_topology()
        self.routing_strategy.setup_routes(self)

    def _setup_docker_nodes(self, start_index, end_index):
        """
        Setup the docker nodes related configurations,
        such as image, volume, and port binding.
        """
        if start_index > end_index:
            return False
        logging.info("Oasis finished Docker nodes setup with num of nodes %s",
                     end_index - start_index + 1)
        for i in range(start_index, end_index + 1):
            if self.node_bind_port:
                port_bindings = {i + 10000: i + 10000}
                ports = [i + 10000]
            else:
                port_bindings = {}
                ports = []
            self.containernet.addDocker(
                f'{self.node_name_prefix}{i}',
                ip=None,
                volumes=self.node_vols,
                cap_add=["NET_ADMIN", "SYS_ADMIN"],
                dimage=self.node_img,
                ports=ports,
                port_bindings=port_bindings,
                publish_all_ports=True
            )
        self.hosts = [ContainernetHostAdapter(host)
                      for host in self.containernet.hosts]
        return True

    def _setup_topology(self):
        """
        Setup the topology of the network by adding routes, links, etc.
        """
        link_subnets = subnets(self.node_ip_start, self.node_ip_range)
        _, link_prefix = netParse(self.node_ip_start)
        # for adjacent matrix, only the upper triangle is used.
        logging.info("Oasis setup the network topology"
                     ", num. of nodes %s, mat size %s",
                     self.num_of_hosts, len(self.net_mat))
        for i in range(self.num_of_hosts):
            for j in range(i, self.num_of_hosts):
                if self.net_mat[i][j] == 1:
                    link_ip = next(link_subnets)
                    left_ip = ipStr(link_ip + 1) + f'/{link_prefix}'
                    right_ip = ipStr(link_ip + 2) + f'/{link_prefix}'
                    logging.info(
                        "addLink: %s(%s) <--> %s(%s)",
                        self.hosts[i].name(),
                        left_ip,
                        self.hosts[j].name(),
                        right_ip
                    )
                    self._addLink(i, j,
                                  params1={'ip': left_ip},
                                  params2={'ip': right_ip}
                                  )
                    self.pair_to_link_ip[(
                        self.hosts[i],
                        self.hosts[j])] = ipStr(link_ip + 2)
                    self.pair_to_link_ip[(
                        self.hosts[j],
                        self.hosts[i])] = ipStr(link_ip + 1)

        for i in range(self.num_of_hosts):
            logging.info("Oasis config ip routing for host %s",
                         self.hosts[i].name())
            self.hosts[i].cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
            self.hosts[i].cmd('sysctl -p')
        logging.info(
            "############### Oasis Init Networking done ###########")
        return True

    def _addLink(
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
        '''
        if self.net_bw_mat is not None:
            params['bw'] = self.net_bw_mat[id1][id2]
        if self.net_loss_mat is not None:
            params['loss'] = self.net_loss_mat[id1][id2]
        if self.net_latency_mat is not None:
            params['delay'] = str(self.net_latency_mat[id1][id2]) + 'ms'
            # params['latency_ms'] = int(self.net_latency_mat[id1][id2])
        if self.net_jitter_mat is not None:
            params['jitter'] = self.net_jitter_mat[id1][id2]
        params['max_queue_size'] = 20000000
        params['use_tbf'] = True
        # apply the traffic shaping on the ingress interface.
        params['ts_on_ingress'] = True
        link = self.containernet.addLink(
            self.hosts[id1].get_host(),
            self.hosts[id2].get_host(),
            port1, port2, cls=TCLink, **params)
        return link

    def _check_node_vols(self):
        if not os.path.exists('/usr/bin/perf') or \
                not os.path.isfile('/usr/bin/perf'):
            logging.warning("perf is not available.")
            self.node_vols = [
                vol for vol in self.node_vols if '/usr/bin/perf' not in vol]

    def _expand_network(self, diff):
        """
        Expand the network by adding more nodes.
        """
        logging.info(
            "Reload the network. number of "
            "nodes increased by %s",
            diff)
        self._reset_network(self.num_of_hosts, diff)
        self._setup_docker_nodes(self.num_of_hosts,
                                 self.num_of_hosts + diff - 1)
        self.num_of_hosts += diff
        self._setup_topology()
        self.routing_strategy.setup_routes(self)
        logging.info(
            "Expand the network. number of nodes increased by %s",
            diff)
        return True

    def _shrink_network(self, diff):
        logging.info(
            "Reload the network. number of "
            "nodes decreased by %s",
            diff)
        self._reset_network(self.num_of_hosts, -diff)
        for i in range(self.num_of_hosts - diff, self.num_of_hosts):
            logging.info("removeDocker: %s", f'{self.node_name_prefix}{i}')
            self.containernet.removeDocker(f'{self.node_name_prefix}{i}')
        # update local hosts list.
        self.hosts = [ContainernetHostAdapter(host)
                      for host in self.containernet.hosts]
        self.num_of_hosts -= diff
        self._setup_topology()
        self.routing_strategy.setup_routes(self)
        return True

    def _reset_network(self, num, diff):
        logging.info("Oasis reset the network.")
        # remove all links
        for i in range(num - 1):
            logging.info("removeLink: %s-%s",
                         self.hosts[i].name(),
                         self.hosts[i+1].name())
            self.containernet.removeLink(
                node1=self.hosts[i].name(),
                node2=self.hosts[i+1].name())
        # remove all routes.
        logging.info("Oasis reset the routes and interfaces.")
        for host in self.hosts:
            host.cmd('ip route flush table main')
            host.deleteIntfs()
            host.cleanup()
        self.net_routes = [range(self.num_of_hosts + diff)]
        self.pair_to_link = {}
        self.pair_to_link_ip = {}
        return True
