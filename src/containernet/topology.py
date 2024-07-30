from abc import ABC, abstractmethod
from enum import IntEnum
import logging
import os
import json
import yaml

from .config import (TopologyConfig, MatrixType)


class LinkAttr(IntEnum):
    link_loss = 0,
    link_latency = 1,
    link_jitter = 2,
    link_bandwidth_forward = 3,
    link_bandwidth_backward = 4


# mapping MatrixType to the link attribute except for the adjacency matrix
MatType2LinkAttr = {
    MatrixType.LOSS_MATRIX: LinkAttr.link_loss,
    MatrixType.LATENCY_MATRIX: LinkAttr.link_latency,
    MatrixType.JITTER_MATRIX: LinkAttr.link_jitter,
    MatrixType.BANDWIDTH_MATRIX: LinkAttr.link_bandwidth_forward
}


class ITopology(ABC):
    def __init__(self) -> None:
        self.all_mats = {}
        self.top_config = None
        self.adj_matrix = None

    @abstractmethod
    def generate_adj_matrix(self, num_of_nodes: int):
        pass

    @abstractmethod
    def generate_other_matrices(self, adj_matrix):
        pass

    def get_matrix(self, mat_type: MatrixType):
        return self.all_mats[mat_type]

    def init_all_matrices(self):
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

    def load_yaml_config(self, yaml_description: str):
        # load it directly from the yaml_description or
        # load it from another yaml file.
        topology = None
        is_load_from_file = ["config_file", "config_name"]
        if all(key in yaml_description for key in is_load_from_file):
            # load from the yaml file `config_file`
            topology = self.load_topology_config(
                yaml_description['config_file'],
                yaml_description['config_name'])
        else:
            # load directly from the yaml_description
            logging.info('load_yaml_config: %s', yaml_description)
            topology = TopologyConfig(**yaml_description)
        return topology

    def load_topology_config(self, yaml_config_file: str,
                             config_name: str) -> TopologyConfig:
        '''
        Load the topology configuration from a yaml file. The configuration 
        contains the following fields:
        - name of the topology
        - number of nodes
        - topology type
        - one of the following:
            - array_description: the array description of the topology
            - json_description: the json description of the topology;
                if json_description is provided, need load the topology 
                from the json file.
        '''
        if not os.path.exists(yaml_config_file):
            logging.error(
                f"load_topology_config: file %s does not exist.",
                yaml_config_file)
            return None
        topology_config = []
        with open(yaml_config_file, 'r', encoding='utf-8') as stream:
            try:
                topology_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)
                return None
        if topology_config is None or "topology" not in topology_config:
            logging.error(
                f"load_topology_config: topology is not defined in %s",
                yaml_config_file)
            return None
        # Find it by 'name' in `topology_config`, for example "linear_network"
        for topology in topology_config['topology']:
            if topology['name'] == config_name:
                loaded_topology = topology
                break
        logging.info('load_topology_config: loaded %s', loaded_topology)
        return TopologyConfig(**loaded_topology)

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
