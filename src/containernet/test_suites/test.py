from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional


class TestType(IntEnum):
    throughput = 0
    latency = 1
    jitter = 2


@dataclass
class TestConfig:
    interval: Optional[float] = field(default=1.0)
    interval_num: Optional[int] = field(default=10)
    log_file: Optional[str] = field(default=None)
    test_type: Optional[TestType] = field(default=TestType.throughput)


class ITestSuite(ABC):
    def __init__(self, config: TestConfig) -> None:
        self.is_success = False
        self.config = config

    @abstractmethod
    def post_process(self):
        pass

    @abstractmethod
    def pre_process(self):
        pass

    @abstractmethod
    def _run_test(self, network: 'Network'):  # type: ignore
        pass

    def run(self, network: 'Network'):  # type: ignore
        self.is_success = self.pre_process()
        if not self.is_success:
            return
        self.is_success = self._run_test(network)
        if not self.is_success:
            return
        self.is_success = self.post_process()
        if not self.is_success:
            return

    def is_succeed(self) -> bool:
        return self.is_success
