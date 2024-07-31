from abc import ABC, abstractmethod
from enum import IntEnum


class TestType(IntEnum):
    throughput = 0
    latency = 1
    jitter = 2


class ITestSuite(ABC):
    def __init__(self) -> None:
        self.is_success = False

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
