import os
import logging
from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass, field
from typing import (Optional, List)


class ProtoType(IntEnum):
    distributed = 0
    none_distributed = 1


proto_type_str_mapping = {
    "distributed": ProtoType.distributed,
    "none_distributed": ProtoType.none_distributed
}


@dataclass
class ProtoConfig:
    name: str = field(default="")
    path: Optional[str] = field(default=None)
    args: Optional[List[str]] = field(default=None)
    version: Optional[str] = field(default=None)
    hosts: Optional[List[int]] = field(default=None)
    port: Optional[int] = field(default=None)
    type: Optional[str] = field(default='distributed')
    test_name: str = field(default="")
    protocols: Optional[List['ProtoConfig']] = field(
        default=None)  # type: ignore


SupportedProto = ['btp', 'brtp', 'brtp_proxy', 'tcp', 'kcp']
SupportedBATSProto = ['btp', 'brtp', 'brtp_proxy']


class IProtoSuite(ABC):
    def __init__(self, config: ProtoConfig):
        self.is_success = False
        self.config = config
        self.log_dir = f"/root/test_results/{self.config.test_name}/{self.config.name}/log/"
        if not os.path.exists(f"{self.log_dir}"):
            os.makedirs(f"{self.log_dir}")

        self.protocol_args = ''
        if self.config.args:
            for arg in self.config.args:
                self.protocol_args += arg + ' '
            logging.info("protocol %s args: %s",
                         self.config.name, self.protocol_args)

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
