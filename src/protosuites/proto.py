import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (Optional, List)


@dataclass
class ProtoConfig:
    name: str = field(default="")
    path: Optional[str] = field(default=None)
    args: Optional[str] = field(default=None)
    version: Optional[str] = field(default='latest')
    hosts: Optional[List[int]] = field(default=None)
    port: Optional[int] = field(default=None)
    role: Optional[str] = field(default='None')


SupportedProtoRole = ['client', 'server', 'None']
SupportedProto = ['btp', 'brtp', 'brtp_proxy', 'tcp', 'kcp']
SupportedBATSProto = ['btp', 'brtp', 'brtp_proxy']


class IProtoSuite(ABC):
    def __init__(self, config: ProtoConfig):
        self.is_success = False
        self.config = config
        self.log_dir = f"/root/test_results/{self.config.name}/log/"
        if not os.path.exists(f"{self.log_dir}"):
            os.makedirs(f"{self.log_dir}")

    def get_config(self) -> ProtoConfig:
        return self.config

    @abstractmethod
    def post_run(self, network: 'INetwork'):  # type: ignore
        pass

    @abstractmethod
    def pre_run(self, network: 'INetwork'):  # type: ignore
        pass

    @abstractmethod
    def run(self, network: 'INetwork'):  # type: ignore
        pass

    def start(self, network: 'INetwork'):  # type: ignore
        self.is_success = self.pre_run(network)
        if not self.is_success:
            return
        self.is_success = self.run(network)
        if not self.is_success:
            return
        self.is_success = self.post_run(network)
        if not self.is_success:
            return

    @abstractmethod
    def stop(self, network: 'INetwork'):  # type: ignore
        pass
