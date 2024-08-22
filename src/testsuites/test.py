import logging
import os
from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional
from protosuites.proto_info import IProtoInfo


class TestType(IntEnum):
    throughput = 0
    latency = 1
    jitter = 2
    rtt = 3


# add mapping for the test type
test_type_str_mapping = {
    TestType.throughput: "throughput",
    TestType.latency: "latency",
    TestType.jitter: "jitter",
    TestType.rtt: "rtt"
}


@dataclass
class TestConfig:
    """
    TestConfig is a dataclass that holds the configuration for the test.
    interval: The interval time for the test.
    interval_num: The number of intervals.
    packet_size: The size of the packet to be sent.
    packet_count: The number of packets to be sent.
    test_type: The type of test to be performed.
    client_host: The host id of the client. 
        for iperf, iperf client will be run on this host.
        if None, iperf client will be run on all hosts.
    server_host: The host id of the server.
        for iperf, iperf server will be run on this host.
        If None, iperf server will be run on all hosts.
    allow_fail: A boolean value that indicates whether the test can fail.
    """
    name: str = field(default="")
    interval: Optional[float] = field(default=1.0)
    interval_num: Optional[int] = field(default=10)
    packet_size: Optional[int] = field(default=1024)
    packet_count: Optional[int] = field(default=10)
    test_type: Optional[TestType] = field(default=TestType.throughput)
    client_host: Optional[int] = field(default=None)
    server_host: Optional[int] = field(default=None)
    allow_fail: Optional[bool] = field(default=False)


@dataclass
class TestResult:
    """
    TestResult is a dataclass that holds the result of the test.
    is_success: A boolean value that indicates whether the test was successful.
    record: The record file generated by the test which contains the test results.
        file name pattern: <class_name>_<test_type>_<client_host>_<server_host>.log
    """
    is_success: bool
    pattern: str
    record: str
    result_dir: str = field(default="/root/")


class ITestSuite(ABC):
    def __init__(self, config: TestConfig) -> None:
        self.config = config
        self.result_dir = f"/root/test_results/{self.config.name}/"
        if not os.path.exists(f"{self.result_dir}"):
            os.makedirs(f"{self.result_dir}")
        self.result = TestResult(
            False, pattern=f"{self.__class__.__name__}_{test_type_str_mapping[self.config.test_type]}"
            f"_h{self.config.client_host}_h{self.config.server_host}.log",
            record="", result_dir=self.result_dir)

    @abstractmethod
    def post_process(self):
        pass

    @abstractmethod
    def pre_process(self):
        pass

    @abstractmethod
    def _run_test(self, network: 'INetwork', proto_info: IProtoInfo):  # type: ignore
        pass

    def run(self, network: 'INetwork', proto_info: IProtoInfo) -> TestResult:  # type: ignore
        if proto_info.get_protocol_version() is not None and proto_info.get_protocol_version() != 'latest':
            if 'tcp' not in proto_info.get_protocol_name():
                base_name = proto_info.get_protocol_name().upper() + "-" + \
                    proto_info.get_protocol_version()
            else:
                base_name = proto_info.get_protocol_name().upper()
        else:
            base_name = proto_info.get_protocol_name().upper()
        self.result.record = self.result.result_dir + \
            base_name + "_" + self.result.pattern
        self.result.is_success = self.pre_process()
        # checking for non-distributed protocols
        if not proto_info.is_distributed():
            if self.config.client_host is None:
                logging.error(
                    "Test non-distributed protocols without client host is not supported.")
                return False
            if self.config.server_host is None:
                logging.error(
                    "Test non-distributed protocols without server host is not supported.")
                return False
            if len(proto_info.get_config().hosts) != 2:
                logging.error(
                    "Test non-distributed protocols, but protocol server/client hosts are not set.")
                return False
            if proto_info.get_config().hosts[0] != self.config.client_host or \
                    proto_info.get_config().hosts[1] != self.config.server_host:
                logging.error(
                    "Test non-distributed protocols, protocol client/server runs on %s/%s, "
                    "but test tools client/server hosts are %s/%s.",
                    proto_info.get_config(
                    ).hosts[0], proto_info.get_config().hosts[1],
                    self.config.client_host, self.config.server_host)
                return False
        if not self.result.is_success:
            return self.result
        self.result.is_success = self._run_test(network, proto_info)
        if not self.result.is_success:
            logging.error("Test %s failed.", self.config.name)
            return self.result
        self.result.is_success = self.post_process()
        if not self.result.is_success:
            return self.result
        return self.result

    def is_succeed(self) -> bool:
        return self.result.is_success

    def type(self) -> TestType:
        return self.config.test_type

    def get_result(self) -> TestResult:
        return self.result

    def get_config(self) -> TestConfig:
        return self.config
