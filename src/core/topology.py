from abc import ABC, abstractmethod
from enum import IntEnum

from dataclasses import dataclass, field
from typing import Optional, List
import logging
import os
import json


class LinkAttr(IntEnum):
    link_loss = 0
    link_latency = 1
    link_jitter = 2
    link_bandwidth_forward = 3
    link_bandwidth_backward = 4


class MatrixType(IntEnum):
    # Adjacency matrix to describe the network topology
    ADJACENCY_MATRIX = 0
    # Bandwidth matrix to describe the network bandwidth link-by-link
    BW_MATRIX = 1
    # Loss matrix to describe the network loss link-by-link
    LOSS_MATRIX = 2
    # Latency matrix to describe the network latency link-by-link
    LATENCY_MATRIX = 3
    # Jitter matrix to describe the network jitter link-by-link
    JITTER_MATRIX = 4


# mapping MatrixType to the link attribute except for the adjacency matrix
MatType2LinkAttr = {
    MatrixType.LOSS_MATRIX: LinkAttr.link_loss,
    MatrixType.LATENCY_MATRIX: LinkAttr.link_latency,
    MatrixType.JITTER_MATRIX: LinkAttr.link_jitter,
    MatrixType.BW_MATRIX: LinkAttr.link_bandwidth_forward
}


class TopologyType(IntEnum):
    linear = 0      # Linear chain topology
    star = 1        # Star topology
    tree = 2        # Complete Binary Tree
    butterfly = 3   # Butterfly topology
    mesh = 5        # Random Mesh topology


@dataclass
class Parameter:
    name: str
    init_value: List[int]


@dataclass
class TopologyConfig:
    """Configuration for the network topology.
    """
    name: str
    nodes: int
    topology_type: TopologyType
    # @array_description: the array description of the topology
    array_description: Optional[List[Parameter]] = field(default=None)
    # @json_description: the json description of the topology
    json_description: Optional[str] = field(default=None)


class ITopology(ABC):
    def __init__(self, base_path: str, top: TopologyConfig, init_all_mat: bool = True):
        self.conf_base_path = base_path
        self.all_mats = {}
        self.adj_matrix = None
        self.top_config = top
        self.compound_top = False
        self._current_top_index = 0  # keep track of the current topology
        # when compound_top is True, the topologies is a list of ITopology;
        # otherwise, it is empty.
        self.topologies = []
        if init_all_mat is True:
            self.init_all_mats()

    def __iter__(self):
        return iter(self.topologies)

    @abstractmethod
    def description(self) -> str:
        pass

    def get_next_top(self):
        if not self.is_compound():
            logging.error("get_next_top() called on a non-compound topology.")
            return None
        if self._current_top_index >= len(self.topologies):
            logging.info("No more compound topologies available.")
            return None
        top = self.topologies[self._current_top_index]
        logging.info("########## Use Oasis compound topology %s.",
                     self._current_top_index)
        self._current_top_index += 1
        return top

    def is_compound(self):
        return self.compound_top

    @abstractmethod
    def generate_adj_matrix(self, num_of_nodes: int):
        pass

    @abstractmethod
    def generate_other_matrices(self, adj_matrix):
        pass

    def get_topology_type(self):
        return self.top_config.topology_type

    def get_matrix(self, mat_type: MatrixType):
        # when invoked, compound_top is expected to be False
        if self.is_compound():
            logging.error("Incorrect usage of compound topology get_matrix()")
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
                src/config/mesh-network.json
        """
        if json_file_path and not os.path.isabs(json_file_path):
            json_file_path = os.path.join(self.conf_base_path, json_file_path)
        logging.info(f"Loading matrix from Json file: %s", json_file_path)
        if not os.path.exists(json_file_path):
            raise ValueError(f"Json File {json_file_path} does not exist.")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
        if json_content is None:
            raise ValueError("The content of the Json file is None.")
        for mat_desc in json_content['data']:
            if 'matrix_type' not in mat_desc or 'matrix_data' not in mat_desc:
                continue
            logging.info(f"Matrix data: %s", mat_desc['matrix_data'])
            self.all_mats[mat_desc['matrix_type']] = mat_desc['matrix_data']
