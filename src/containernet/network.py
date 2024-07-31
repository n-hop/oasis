import logging
from mininet.net import Containernet
from mininet.util import ipStr, netParse
from mininet.link import TCLink
from containernet.topology import (ITopology, MatrixType)
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
        self.first_link_ip = '10.0.0.0/24'
        # NodeConfig: Docker node related
        self.node_img = node_config.node_img
        self.node_vols = node_config.node_vols
        self.node_bind_port = node_config.node_bind_port
        self.node_name_prefix = node_config.node_name_prefix
        self.node_ip_range = node_config.node_ip_range
        # Topology related
        self.net_mat = net_topology.get_matrix(MatrixType.ADJACENCY_MATRIX)
        self.net_link_loss_mat = net_topology.get_matrix(
            MatrixType.LOSS_MATRIX)
        self.net_link_bw_mat = net_topology.get_matrix(
            MatrixType.BANDWIDTH_MATRIX)
        self.net_link_latency_mat = net_topology.get_matrix(
            MatrixType.LATENCY_MATRIX)
        self.net_link_jitter_mat = net_topology.get_matrix(
            MatrixType.JITTER_MATRIX)
        logging.info('self.net_mat %s', self.net_mat)
        logging.info('self.net_link_loss_mat %s', self.net_link_loss_mat)
        logging.info('self.net_link_bw_mat %s', self.net_link_bw_mat)
        logging.info('self.net_link_latency_mat %s', self.net_link_latency_mat)
        logging.info('self.net_link_jitter_mat %s', self.net_link_jitter_mat)

        if self.net_mat is not None:
            self.num_of_hosts = len(self.net_mat)
        else:
            raise ValueError('The topology matrix is None.')
        self.net_routes = [range(self.num_of_hosts)]
        self.route_table = {}
        logging.info('self.node_vols %s', self.node_vols)
        self._init_containernet()

    def get_hosts(self):
        return self.hosts

    def get_route_table(self) -> dict:
        return self.route_table

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
        link_subnets = subnets(self.first_link_ip, self.node_ip_range)
        _, link_prefix = netParse(self.first_link_ip)
        # for adjacent matrix, only the upper triangle is used.
        for i in range(self.num_of_hosts):
            for j in range(i+1, self.num_of_hosts):
                if self.net_mat[i][j] == 1:
                    link_ip = next(link_subnets)
                    left_ip = ipStr(link_ip + 1) + f'/{link_prefix}'
                    right_ip = ipStr(link_ip + 2) + f'/{link_prefix}'
                    self.__addLink(i, j,
                                   params1={'ip': left_ip},
                                   params2={'ip': right_ip}
                                   )
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
            delay="100ms", bw=1, loss=10, jitter=5)
        # FIXME: Warning: sch_htb: quantum of \
            class 50001 is big. Consider r2q change.
        '''
        if self.net_link_bw_mat is not None:
            params['bw'] = self.net_link_bw_mat[id1][id2]
        if self.net_link_loss_mat is not None:
            params['loss'] = self.net_link_loss_mat[id1][id2]
        if self.net_link_latency_mat is not None:
            params['delay'] = str(self.net_link_latency_mat[id1][id2]) + 'ms'
        if self.net_link_jitter_mat is not None:
            params['jitter'] = self.net_link_jitter_mat[id1][id2]
        link = super().addLink(
            self.hosts[id1], self.hosts[id2],
            port1, port2, cls=TCLink, **params)
        logging.info(
            "addLink: %s(%s) <--> %s(%s)",
            self.hosts[id1].name,
            self.hosts[id1].IP(),
            self.hosts[id2].name,
            self.hosts[id2].IP()
        )
        return link

    def _setup_routes(self):
        # setup routes
        # 1. ip config
        # 2. OLSR config
        pass
