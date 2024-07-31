"""
    A Wrapper for the mininet Host (Node)

"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from enum import IntEnum
import logging
import os
import yaml


class MatrixType(IntEnum):
    # Adjacency matrix to describe the network topology
    ADJACENCY_MATRIX = 0
    # Bandwidth matrix to describe the network bandwidth link-by-link
    BANDW_MATRIX = 1
    # Loss matrix to describe the network loss link-by-link
    LOSS_MATRIX = 2
    # Latency matrix to describe the network latency link-by-link
    LATENCY_MATRIX = 3
    # Jitter matrix to describe the network jitter link-by-link
    JITTER_MATRIX = 4


class TopologyType(IntEnum):
    linear = 0      # Linear chain topology
    star = 1        # Star topology
    tree = 2        # Complete Binary Tree
    butterfly = 3   # Butterfly topology
    mesh = 5        # Random Mesh topology


@dataclass
class NodeConfig:
    """Configuration for the Docker node.
    """
    name: str
    node_img: str
    node_vols: Optional[list] = field(default=None)
    node_bind_port: Optional[bool] = field(default=True)
    node_name_prefix: Optional[str] = field(default='h')
    node_ip_range: Optional[str] = field(default='10.0.0.0/8')
    node_route: Optional[str] = field(default='ip')


@dataclass
class NestedConfig:
    """
    NestedConfig is a dataclass that holds
    the configuration for the Nested Containernet.
    """
    image: str
    privileged: Optional[bool] = field(default=True)
    network_mode: Optional[str] = field(default="host")
    dns_server: Optional[List[str]] = field(default=None)
    dns_resolve: Optional[List[str]] = field(default=None)
    mounts: Optional[List[str]] = field(default=None)


@dataclass
class Parameter:
    array: List[int]


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


class INodeConfig(ABC):
    @staticmethod
    def load_node_config(yaml_config_file: str,
                         config_name: str) -> NodeConfig:
        if not os.path.exists(yaml_config_file):
            logging.error(
                f"load_node_config: file %s does not exist.",
                yaml_config_file)
            return None
        node_config = []
        with open(yaml_config_file, 'r', encoding='utf-8') as stream:
            try:
                node_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)
                return None
        if node_config is None or "node" not in node_config:
            logging.error(
                f"load_node_config: node config is not defined in %s",
                yaml_config_file)
            return None
        # Find it by 'name' in `node_config`, for example "linear_network"
        for topology in node_config['node']:
            if topology['name'] == config_name:
                loaded_node_config = topology
                break
        logging.info('load_node_config: loaded %s', loaded_node_config)
        return NodeConfig(**loaded_node_config)

    @staticmethod
    def load_yaml_config(yaml_description: str):
        # load it directly from the yaml_description or
        # load it from another yaml file.
        node_config = None
        is_load_from_file = ["config_file", "config_name"]
        if all(key in yaml_description for key in is_load_from_file):
            # load from the yaml file `config_file`
            node_config = INodeConfig.load_node_config(
                yaml_description['config_file'],
                yaml_description['config_name'])
        else:
            # load directly from the yaml_description
            logging.info('load_yaml_config: %s', yaml_description)
            node_config = NodeConfig(**yaml_description)
        return node_config
