from abc import ABC, abstractmethod
from enum import IntEnum
import logging
import os
import json
from .config import (TopologyConfig, MatrixType)


class LinkAttr(IntEnum):
    link_loss = 0
    link_latency = 1
    link_jitter = 2
    link_bandwidth_forward = 3
    link_bandwidth_backward = 4


# mapping MatrixType to the link attribute except for the adjacency matrix
MatType2LinkAttr = {
    MatrixType.LOSS_MATRIX: LinkAttr.link_loss,
    MatrixType.LATENCY_MATRIX: LinkAttr.link_latency,
    MatrixType.JITTER_MATRIX: LinkAttr.link_jitter,
    MatrixType.UPLINK_BANDW_MATRIX: LinkAttr.link_bandwidth_forward,
    MatrixType.DOWNLINK_BANDW_MATRIX: LinkAttr.link_bandwidth_backward
}


class ITopology(ABC):
    def __init__(self, top: TopologyConfig) -> None:
        self.all_mats = {}
        self.adj_matrix = None
        self.top_config = top
        self.init_all_mats()

    @abstractmethod
    def generate_adj_matrix(self, num_of_nodes: int):
        pass

    @abstractmethod
    def generate_other_matrices(self, adj_matrix):
        pass

    def get_topology_type(self):
        return self.top_config.topology_type

    def get_matrix(self, mat_type: MatrixType):
        if mat_type not in self.all_mats:
            return None
        return self.all_mats[mat_type]

    def init_all_mats(self):
        # init from json_description or array_description
        if self.top_config.json_description is not None:
            logging.info(
                'Load the matrix from json_description')
            self.load_all_mats(
                self.top_config.json_description)
        elif self.top_config.array_description is not None:
            logging.info(
                'Load the matrix from array_description')
            self.adj_matrix = self.generate_adj_matrix(self.top_config.nodes)
            self.all_mats[MatrixType.ADJACENCY_MATRIX] = self.adj_matrix
            self.generate_other_matrices(self.adj_matrix)

    def load_all_mats(self, json_file_path):
        """Load all matrices from the Json file.
        Args:
            json_file_path (string): The path of the Json file 
            which save the matrix.
            An example: 
                test_framework/template_topology/4-child-star-network.json
        """
        if json_file_path is None or not os.path.exists(json_file_path):
            raise ValueError(f"Json File {json_file_path} does not exist.")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
        if json_content is None:
            raise ValueError("The content of the Json file is None.")
        for mat_desc in json_content['data']:
            if 'matrix_type' not in mat_desc or 'matrix_data' not in mat_desc:
                continue
            # logging.info(f"Matrix data: {mat_desc['matrix_data']}")
            self.all_mats[mat_desc['matrix_type']] = mat_desc['matrix_data']
