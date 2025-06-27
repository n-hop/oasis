import logging
import copy
from .topology import (ITopology, MatrixType)


class MeshTopology(ITopology):
    def __init__(self, base_path: str, top_config, init_all_mats=True):
        super().__init__(base_path, top_config, init_all_mats)
        if init_all_mats is True:
            self.__init_topologies()

    def description(self) -> str:
        nodes_num = len(self.all_mats[MatrixType.ADJACENCY_MATRIX][0])
        description = f"Mesh {nodes_num} nodes \n"
        latency = self.all_mats[MatrixType.LATENCY_MATRIX][0][1]
        bandwidth = self.all_mats[MatrixType.BW_MATRIX][0][1]
        for i in range(nodes_num):
            for j in range(nodes_num):
                if self.all_mats[MatrixType.BW_MATRIX][i][j] > 0:
                    latency = self.all_mats[MatrixType.LATENCY_MATRIX][i][j]
                    bandwidth = self.all_mats[MatrixType.BW_MATRIX][i][j]
                    break
        description += f"latency {latency}ms,"
        description += f"bandwidth {bandwidth}Mbps."
        return description

    def generate_adj_matrix(self, num_of_nodes: int):
        pass

    def generate_other_matrices(self, adj_matrix):
        pass

    def __init_topologies(self):
        self.compound_top = True
        # purpose: for iterating through multiple topologies
        the_unique_topology = MeshTopology(self.conf_base_path,
                                           self.top_config, False)  # don't init all mats
        the_unique_topology.all_mats[MatrixType.ADJACENCY_MATRIX] = copy.deepcopy(
            self.all_mats[MatrixType.ADJACENCY_MATRIX])
        the_unique_topology.all_mats[MatrixType.LOSS_MATRIX] = copy.deepcopy(
            self.all_mats[MatrixType.LOSS_MATRIX])
        the_unique_topology.all_mats[MatrixType.LATENCY_MATRIX] = copy.deepcopy(
            self.all_mats[MatrixType.LATENCY_MATRIX])
        the_unique_topology.all_mats[MatrixType.JITTER_MATRIX] = copy.deepcopy(
            self.all_mats[MatrixType.JITTER_MATRIX])
        the_unique_topology.all_mats[MatrixType.BW_MATRIX] = copy.deepcopy(
            self.all_mats[MatrixType.BW_MATRIX])
        logging.info(
            "Added MeshTopology %s", the_unique_topology.all_mats)
        self.topologies.append(the_unique_topology)
