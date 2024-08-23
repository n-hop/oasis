from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StorageConfig:
    name: str


class IDataStorage(ABC):
    def __init__(self, config: StorageConfig):
        super().__init__()
        self.config = config

    @abstractmethod
    def store(self):
        pass

    @abstractmethod
    def load(self):
        pass
