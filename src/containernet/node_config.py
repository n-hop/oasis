"""
    A Wrapper for the mininet Host (Node)

"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeConfig:
    node_img: str
    node_vols: Optional[list] = field(default=None)
    node_bind_port: Optional[bool] = field(default=True)
    node_name_prefix: Optional[str] = field(default='h')
    node_ip_range: Optional[str] = field(default='10.0.0.0/8')
