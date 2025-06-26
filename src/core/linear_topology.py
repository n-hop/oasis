import logging
import copy

from .topology import (ITopology, MatrixType, MatType2LinkAttr, LinkAttr)

max_link_bandwidth = 4000
max_link_latency = 200


class LinearTopology(ITopology):
    def __init__(self, base_path: str, top_config, init_all_mats=True):
        super().__init__(base_path, top_config, init_all_mats)

    def generate_adj_matrix(self, num_of_nodes: int):
        """
        Generate the adjacency matrix to describe a linear chain topology.
                only 0 and 1 are used to describe the link.
        Args:
            num_of_nodes (int): The number of nodes in the network.
                In a linear chain topology, the number of nodes minus 1 is
                the number of hops.
        """
        hops = num_of_nodes - 1
        logging.info("Generate a %d-hops linear chain topology. %d",
                     hops, num_of_nodes)
        # Generate the adjacency matrix for the linear chain topology
        adj_matrix = [[0 for _ in range(num_of_nodes)]
                      for _ in range(num_of_nodes)]
        for i in range(num_of_nodes):
            if i == 0:
                adj_matrix[i][i+1] = 1
            elif i == num_of_nodes - 1:
                adj_matrix[i][i-1] = 1
            else:
                adj_matrix[i][i-1] = 1
                adj_matrix[i][i+1] = 1
        logging.debug("adj_matrix: %s", adj_matrix)
        return adj_matrix

    def generate_other_matrices(self, adj_matrix):
        temp_all_mats = {}
        for type in MatrixType:
            if type == MatrixType.ADJACENCY_MATRIX:
                continue
            temp_all_mats[type] = self.generate_value_matrix(
                adj_matrix, type)
        # combination of all types of matrices
        for loss_mat in temp_all_mats[MatrixType.LOSS_MATRIX]:
            for latency_mat in temp_all_mats[MatrixType.LATENCY_MATRIX]:
                for jitter_mat in temp_all_mats[MatrixType.JITTER_MATRIX]:
                    for bandw_mat in temp_all_mats[MatrixType.BANDW_MATRIX]:
                        new_topology = LinearTopology(self.conf_base_path,
                                                      self.top_config, False)  # don't init all mats
                        new_topology.all_mats[MatrixType.ADJACENCY_MATRIX] = copy.deepcopy(
                            self.adj_matrix)
                        new_topology.all_mats[MatrixType.LOSS_MATRIX] = copy.deepcopy(
                            loss_mat)
                        new_topology.all_mats[MatrixType.LATENCY_MATRIX] = copy.deepcopy(
                            latency_mat)
                        new_topology.all_mats[MatrixType.JITTER_MATRIX] = copy.deepcopy(
                            jitter_mat)
                        new_topology.all_mats[MatrixType.BANDW_MATRIX] = copy.deepcopy(
                            bandw_mat)
                        logging.debug(
                            "Added new_topology %s", new_topology.all_mats)
                        self.topologies.append(new_topology)

    def generate_value_matrix(self, adj_matrix, type: MatrixType):
        value_mat = copy.deepcopy(adj_matrix)
        if self.top_config.array_description is None:
            logging.warning("No array_description in the topology config")
            return value_mat
        link_bandwidth_backward_dict = None
        for param in self.top_config.array_description:
            if not isinstance(param, dict):
                param = param.__dict__
            if 'link_bandwidth_backward' in param:
                link_bandwidth_backward_dict = param
                break
        for param in self.top_config.array_description:
            if not isinstance(param, dict):
                param = param.__dict__
            for attr_name in param:
                if attr_name in LinkAttr.__members__ and \
                        MatType2LinkAttr[type] == LinkAttr[attr_name]:
                    init_value = param["init_value"]
                    can_be_stepped = False
                    if len(init_value) != self.top_config.nodes:
                        value_mat = [[
                            init_value[0]
                            if value != 0 else value for value in row
                        ] for row in value_mat]
                        can_be_stepped = True
                    elif len(init_value) == self.top_config.nodes:
                        value_mat = [
                            [init_value[i][0] if value != 0 else value for i,
                             value in enumerate(row)] for row in value_mat]
                    if attr_name == "link_bandwidth_forward" and link_bandwidth_backward_dict is not None:
                        logging.debug(
                            "needs to add link_bandwidth_backward %s", link_bandwidth_backward_dict)
                        reverse_value = link_bandwidth_backward_dict["init_value"]
                        mat_size = len(value_mat)
                        for i in range(0, mat_size - 1):
                            value_mat[i+1][i] = reverse_value[i] if i < len(
                                reverse_value) else reverse_value[0]
                    if attr_name == 'link_latency':
                        self.limit_max_value(
                            value_mat, attr_name, max_link_latency)
                    if 'link_bandwidth' in attr_name:
                        self.limit_max_value(
                            value_mat, attr_name, max_link_bandwidth)
                    step_len = 0
                    step_num = 0
                    if can_be_stepped:
                        # can be stepped only when the init_value is a single value
                        step_len = param.get("step_len", 0)
                        step_num = param.get("step_num", 0)
                    logging.info(
                        "############## value_matrix: %s, step_len %s, step_num %s", value_mat, step_len, step_num)
                    if step_len > 0 and step_num > 0:
                        self.compound_top = True
                        return self.step_value_matrix(
                            value_mat, step_len, step_num)
                    # else
                    return [value_mat]
        return [value_mat]

    def step_value_matrix(self, value_mat, step_len, step_num):
        if self.adj_matrix is None:
            logging.error("The adjacency matrix is None")
            return None
        new_value_mat = []
        new_value_mat.append(copy.deepcopy(value_mat))
        for step in range(1, step_num + 1):
            stepped_matrix = []
            for i in range(len(value_mat)):
                row = []
                for j in range(len(value_mat[i])):
                    if self.adj_matrix[i][j] == 1:
                        row.append(value_mat[i][j] + step * step_len)
                    else:
                        row.append(value_mat[i][j])
                stepped_matrix.append(row)
            new_value_mat.append(stepped_matrix)

        return new_value_mat

    def limit_max_value(self, value_mat, attr_name, max_value):
        for i in range(len(value_mat)):
            for j in range(len(value_mat)):
                if i == j:
                    continue
                if value_mat[i][j] > max_value:
                    logging.error(
                        "The %s value is too large, "
                        "it should be less than %s "
                        "The current value is %d", attr_name, max_value, value_mat[i][j])
                value_mat[i][j] = min(value_mat[i][j], max_value)
