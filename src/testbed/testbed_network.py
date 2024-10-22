import logging
from typing import List
from containernet.topology import (ITopology, MatrixType)
from interfaces.network import INetwork
from interfaces.routing import IRoutingStrategy
from testbed.linux_host import LinuxHost
from .config import (HostConfig)


class TestbedNetwork (INetwork):
    """
    Try to connect to a testbed network, then set up the routes and traffic shaping.
    """

    def __init__(self,
                 hosts_config: List[HostConfig],
                 net_topology: ITopology,
                 routing_strategy: IRoutingStrategy,
                 ** params) -> None:
        super().__init__(**params)
        self.routing_strategy = routing_strategy
        self.hosts = []
        self.hosts_conf = hosts_config
        # Topology related
        self._init_matrix(net_topology)
        if self.net_mat is not None:
            self.num_of_hosts = len(self.net_mat)
        else:
            raise ValueError('The topology matrix is None.')
        self.net_routes = [range(self.num_of_hosts)]
        self.test_suites = []
        self._init()

    def get_hosts(self):
        return self.hosts

    def get_num_of_host(self):
        return self.num_of_hosts

    def get_host_ip_range(self):
        pass

    def get_routing_strategy(self):
        return self.routing_strategy

    def get_topology_description(self):
        if self.net_loss_mat is None or self.net_bw_mat is None or \
                self.net_latency_mat is None or self.net_jitter_mat is None:
            logging.warning(
                "The network matrices are not initialized; and traffic shaping will not be applied.")
            return ""
        return ""

    def start(self):
        logging.info("Oasis starts the TestbedNetwork.")
        self.is_started_flag = True

    def stop(self):
        self.routing_strategy.teardown_routes(self)
        self.is_started_flag = False

    def reload(self, top: ITopology):
        """
        Reload the network with new configurations.
        """
        if self._check_topology_change(top):
            self._init_matrix(top)
            self._init()

    def get_link_table(self):
        return {}

    def _check_topology_change(self, top: ITopology):
        is_changed = False
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
        if is_changed is False:
            logging.info("Oasis detected the topology no change.")
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

    def _init(self):
        self.hosts = []
        if len(self.hosts_conf) != self.num_of_hosts:
            raise ValueError(
                "The number of hosts is not equal to the number of hosts in the topology.")
        for host_conf in self.hosts_conf:
            self.hosts.append(LinuxHost(host_conf))
        for host in self.hosts:
            if not host.is_connected():
                self.is_accessible_flag = False
                break
        self.routing_strategy.setup_routes(self)

        def __set_bw_limit_on(host, attached_inf, bw_limit):
            host.cmd(
                f"tc qdisc add dev {attached_inf} root handle 1: {bw_limit}")
            logging.info(
                "apply bandwidth limit on egress interface %s with %s", attached_inf, bw_limit)
            return True
        default_queueing_strategy = "pfifo"

        for id1 in range(self.num_of_hosts):
            for id2 in range(id1, self.num_of_hosts):
                bw_limit1 = default_queueing_strategy
                bw_limit2 = default_queueing_strategy
                if self.net_bw_mat is not None:
                    # bw from host1 to host2
                    bw_limit1 = f"tbf rate {self.net_bw_mat[id1][id2]}mbit"
                    bw_limit1 += f" burst {self.net_bw_mat[id1][id2]*1.25}kb latency 1ms"
                    # bw from host2 to host1
                    bw_limit2 = f"tbf rate {self.net_bw_mat[id2][id1]}mbit"
                    bw_limit2 += f" burst {self.net_bw_mat[id2][id1]*1.25}kb latency 1ms"
                # connection: host1 (eth1)<->(eth0) host2
                __set_bw_limit_on(
                    self.hosts[id1], self.hosts[id1].intf_list[1], bw_limit1)
                __set_bw_limit_on(
                    self.hosts[id2], self.hosts[id2].intf_list[0], bw_limit2)
                # direction from host1 to host2, setup ifb on host2
                self._traffic_shaping_on_ingress(
                    id1, id2, self.hosts[id2].intf_list[0])
                # direction from host2 to host1, setup ifb on host1
                self._traffic_shaping_on_ingress(
                    id2, id1, self.hosts[id1].intf_list[1])

    def _traffic_shaping_on_ingress(self, id1, id2, attached_inf):
        """
        Apply the traffic shaping(latency,jitter,loss) on the ingress interface.
        id1: the source host id.
        id2: the destination host id. Do the traffic shaping on `host2`.
        attached_inf: the interface to be set with the traffic shaping. 

        Details of traffic shaping in Oasis, please refer to <docs/tc-strategy.md>
        """
        shaping_parameters = ""
        if self.net_loss_mat is not None:
            shaping_parameters += f" loss {self.net_loss_mat[id1][id2]}%"
        if self.net_latency_mat is not None:
            delay = self.net_latency_mat[id1][id2]
            if delay > 0:
                shaping_parameters += f" delay {delay}ms"
                if self.net_jitter_mat is not None:
                    jitter = self.net_jitter_mat[id1][id2]
                    if jitter > 0:
                        shaping_parameters += f" {self.net_jitter_mat[id1][id2]}ms distribution normal"
        logging.info("shaping_parameters\"%s\"", shaping_parameters)
        port = attached_inf[-1]
        ifb_interface = f"ifb{port}"
        self.hosts[id2].cmd(
            f"ip link add name {ifb_interface} type ifb")
        self.hosts[id2].cmd(f"ip link set {ifb_interface} up")
        self.hosts[id2].cmd(
            f"tc qdisc add dev {attached_inf} ingress")
        self.hosts[id2].cmd(f"tc filter add dev {attached_inf} parent ffff: protocol ip u32 "
                            f"match u32 0 0 action mirred egress redirect dev {ifb_interface}")
        self.hosts[id2].cmd(
            f"tc qdisc add dev {ifb_interface} root netem{shaping_parameters} limit 30000000")

        return True
