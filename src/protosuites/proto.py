from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (Optional, List)


@dataclass
class ProtoConfig:
    protocol_path: Optional[str] = field(default=None)
    protocol_args: Optional[str] = field(default=None)
    log_file: Optional[str] = field(default=None)
    hosts: Optional[List[int]] = field(default=None)
    port: Optional[int] = field(default=None)


class IProtoSuite(ABC):
    def __init__(self, config: ProtoConfig) -> None:
        self.is_success = False
        self.config = config

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
