import logging
import copy
from .topology import (ITopology, MatrixType, MatType2LinkAttr, LinkAttr)


class LinearTopology(ITopology):

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
        logging.info("adj_matrix: %s", adj_matrix)
        return adj_matrix

    def generate_other_matrices(self, adj_matrix):
        for type in MatrixType:
            if type == MatrixType.ADJACENCY_MATRIX:
                continue
            self.all_mats[type] = self.generate_value_matrix(
                adj_matrix, type)

    def generate_value_matrix(self, adj_matrix, type: MatrixType):
        value_mat = copy.deepcopy(adj_matrix)
        for param in self.top_config.array_description:
            for attr_name in param:
                if attr_name in LinkAttr.__members__ and \
                        MatType2LinkAttr[type] == LinkAttr[attr_name]:
                    init_value = param["init_value"]
                    if len(init_value) != self.top_config.nodes:
                        value_mat = [[
                            init_value[0]
                            if value != 0 else value for value in row
                        ] for row in value_mat]
                    elif len(init_value) == self.top_config.nodes:
                        value_mat = [
                            [init_value[i][0] if value != 0 else value for i,
                             value in enumerate(row)] for row in value_mat]
                    # logging.info("value_matrix: %s", value_mat)
                    return value_mat
        return value_mat
