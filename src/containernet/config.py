"""
    A Wrapper for the mininet Host (Node)

"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import IntEnum


class MatrixType(IntEnum):
    # Adjacency matrix to describe the network topology
    ADJACENCY_MATRIX = 0,
    # Bandwidth matrix to describe the network bandwidth link-by-link
    BANDWIDTH_MATRIX = 1,
    # Loss matrix to describe the network loss link-by-link
    LOSS_MATRIX = 2,
    # Latency matrix to describe the network latency link-by-link
    LATENCY_MATRIX = 3,
    # Jitter matrix to describe the network jitter link-by-link
    JITTER_MATRIX = 4,


class TopologyType(IntEnum):
    linear = 0,     # Linear chain topology
    star = 1,       # Star topology
    tree = 2,       # Complete Binary Tree
    butterfly = 3,  # Butterfly topology
    mesh = 5        # Random Mesh topology


@dataclass
class NodeConfig:
    """Configuration for the Docker node.
    """
    node_img: str
    node_vols: Optional[list] = field(default=None)
    node_bind_port: Optional[bool] = field(default=True)
    node_name_prefix: Optional[str] = field(default='h')
    node_ip_range: Optional[str] = field(default='10.0.0.0/8')


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
