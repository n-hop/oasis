import os
import logging
from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass, field
from typing import (Optional, List)
from protosuites.proto_info import IProtoInfo
from var.global_var import g_root_path


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
    config_file: Optional[str] = field(default=None)
    version: Optional[str] = field(default="")
    hosts: Optional[List[int]] = field(default=None)
    port: Optional[int] = field(default=0)
    type: Optional[str] = field(default='distributed')
    test_name: str = field(default="")
    protocols: Optional[List['ProtoConfig']] = field(default=None)
    config_base_path: Optional[str] = field(default=None)


SupportedProto = ['btp', 'brtp', 'brtp_proxy', 'tcp', 'kcp', 'quic']
SupportedBATSProto = ['btp', 'brtp', 'brtp_proxy']


class IProtoSuite(IProtoInfo, ABC):
    def __init__(self, config: ProtoConfig):
        self.is_success = False
        self.config = config
        self.log_dir = f"{g_root_path}test_results/{self.config.test_name}/{self.config.name}/log/"
        if not os.path.exists(f"{self.log_dir}"):
            os.makedirs(f"{self.log_dir}")

        self.protocol_args: str = ''
        if self.config.args:
            for arg in self.config.args:
                self.protocol_args += arg + ' '
            logging.info("protocol %s args: %s",
                         self.config.name, self.protocol_args)
        self.process_name = None
        if self.config.path:
            self.process_name = os.path.basename(self.config.path)
            if self.process_name == self.config.path:
                logging.info("protocol %s path is a process name.",
                             self.config.path)
            else:
                if not os.path.isfile(f"{g_root_path}{self.config.path}"):
                    # it is in protocol docker image.
                    logging.warning("protocol %s binary %s is not found.",
                                    self.config.name, self.config.path)

    def get_config(self) -> ProtoConfig:
        return self.config

    @abstractmethod
    def post_run(self, network: 'INetwork') -> bool:  # type: ignore
        pass

    @abstractmethod
    def pre_run(self, network: 'INetwork') -> bool:  # type: ignore
        pass

    @abstractmethod
    def run(self, network: 'INetwork') -> bool:  # type: ignore
        pass

    def start(self, network: 'INetwork') -> bool:  # type: ignore
        self.is_success = self.pre_run(network)
        if not self.is_success:
            logging.debug("pre_run failed")
            return False
        self.is_success = self.run(network)
        if not self.is_success:
            logging.debug("run failed")
            return False
        self.is_success = self.post_run(network)
        if not self.is_success:
            logging.debug("post_run failed")
            return False
        return True

    @abstractmethod
    def stop(self, network: 'INetwork'):  # type: ignore
        pass
