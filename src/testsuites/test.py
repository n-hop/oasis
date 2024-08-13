import logging
from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional
from protosuites.proto_info import IProtoInfo


class TestType(IntEnum):
    throughput = 0
    latency = 1
    jitter = 2


@dataclass
class TestConfig:
    """
    TestConfig is a dataclass that holds the configuration for the test.
    interval: The interval time for the test.
    interval_num: The number of intervals.
    packet_size: The size of the packet to be sent.
    packet_count: The number of packets to be sent.
    log_file: The file to log the test results.
    test_type: The type of test to be performed.
    client_host: The host id of the client. 
        for iperf, iperf client will be run on this host.
        if None, iperf client will be run on all hosts.
    server_host: The host id of the server.
        for iperf, iperf server will be run on this host.
        If None, iperf server will be run on all hosts.
    """
    interval: Optional[float] = field(default=1.0)
    interval_num: Optional[int] = field(default=10)
    packet_size: Optional[int] = field(default=1024)
    packet_count: Optional[int] = field(default=10)
    log_file: Optional[str] = field(default=None)
    test_type: Optional[TestType] = field(default=TestType.throughput)
    client_host: Optional[int] = field(default=None)
    server_host: Optional[int] = field(default=None)


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
    def _run_test(self, network: 'INetwork', proto: IProtoInfo):  # type: ignore
        pass

    def run(self, network: 'INetwork', proto: IProtoInfo):  # type: ignore
        self.is_success = self.pre_process()
        if not self.is_success:
            return
        self.is_success = self._run_test(network, proto)
        if not self.is_success:
            logging.error("Test failed.")
            return
        self.is_success = self.post_process()
        if not self.is_success:
            return

    def is_succeed(self) -> bool:
        return self.is_success

    def type(self) -> TestType:
        return self.config.test_type

    def log_file(self) -> str:
        return self.config.log_file
