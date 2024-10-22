"""
    A Wrapper for the mininet Host (Node)

"""
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
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
    img: str
    vols: List[str] = field(default_factory=list)
    bind_port: Optional[bool] = field(default=True)
    name_prefix: Optional[str] = field(default='h')  # h i j k.
    ip_range: Optional[str] = field(default='10.0.0.0/8')


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


supported_config_keys = ["topology", "node_config"]


class IConfig(ABC):
    @staticmethod
    def is_supported_config_key(config_key: str):
        return config_key in supported_config_keys

    @staticmethod
    def load_config_reference(config_base_path: str, yaml_config_file: str,
                              config_name: str, config_key: str):
        if not IConfig.is_supported_config_key(config_key):
            logging.error(
                f"load_config_reference: key %s is not supported.",
                config_key)
            return None
        full_yaml_config_file = os.path.join(
            config_base_path, yaml_config_file)
        if not os.path.exists(full_yaml_config_file):
            logging.error(
                f"load_config_reference: file %s does not exist.",
                full_yaml_config_file)
            return None
        loaded_yaml_config = []
        with open(full_yaml_config_file, 'r', encoding='utf-8') as stream:
            try:
                loaded_yaml_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)
                return None
        # check key 'config_key' in the yaml content
        if loaded_yaml_config is None or config_key not in loaded_yaml_config:
            logging.error(
                f"load_config_reference: %s is not defined in %s",
                config_key, full_yaml_config_file)
            return None
        loaded_config = None
        # Find it by 'name' in `node_config`, for example "linear_network"
        for conf in loaded_yaml_config[config_key]:
            if conf['name'] == config_name:
                loaded_config = conf
                logging.info('load_config_reference: loaded %s', loaded_config)
                break
        if loaded_config is None:
            logging.error(
                f"load_config_reference: %s is not defined in %s",
                config_name, full_yaml_config_file)
            return None
        if config_key == "node_config":
            return NodeConfig(**loaded_config)
        if config_key == "topology":
            return TopologyConfig(**loaded_config)
        return None

    @staticmethod
    def load_yaml_config(config_base_path: str, yaml_description: Dict[str, Any], config_key: str):
        # load it directly from the yaml_description or
        # load it from another yaml file.
        if not IConfig.is_supported_config_key(config_key):
            logging.error(
                f"load_yaml_config: key %s is not supported.",
                config_key)
            return None
        is_load_from_file = ["config_file", "config_name"]
        if all(key in yaml_description for key in is_load_from_file):
            # load from the yaml file `config_file`
            return IConfig.load_config_reference(
                config_base_path,
                yaml_description['config_file'],
                yaml_description['config_name'],
                config_key)
        # load directly from the yaml_description
        logging.info('load_yaml_config: %s', yaml_description)
        if config_key == "node_config":
            return NodeConfig(**yaml_description)
        if config_key == "topology":
            return TopologyConfig(**yaml_description)
        return None
