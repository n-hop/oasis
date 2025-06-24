import logging
import random
import time
import multiprocessing
from dataclasses import dataclass, field
from typing import Optional, List
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite)


@dataclass
class FlowParameter:
    flow_type: str = field(default="tcp")
    client_host: int = field(default=0)
    server_host: int = field(default=1)


@dataclass
class FlowCompetitionConfig:
    competition_flow: Optional[List[FlowParameter]] = field(default=None)


class CompetitionFlowTest(ITestSuite):
    '''
    Decorator of ITestSuite to run competition flows between hosts in the network.
    '''

    def __init__(self, config: FlowCompetitionConfig, test: ITestSuite) -> None:
        '''init with a ITestSuite object
        '''
        super().__init__(test.config)
        self.competition_flows = config.competition_flow if config.competition_flow is not None else []
        self.test = test
        self.min_start = 0
        interval = test.config.interval if test.config.interval is not None else 1
        interval_num = test.config.interval_num if test.config.interval_num is not None else 10
        self.max_interval = interval * interval_num
        self.max_start = min(self.max_interval, 10)
        self.min_duration = 10
        self.max_duration = 20

    def _run_test(self, network: INetwork, proto_info: IProtoInfo):
        processes = []
        start_barrier = multiprocessing.Barrier(
            len(self.competition_flows) + 1)
        for flow in self.competition_flows:
            t = multiprocessing.Process(target=self.run_flow,
                                        args=(flow, network, start_barrier))
            t.start()
            processes.append(t)
        # Wait for all processes to be ready
        start_barrier.wait()
        self.test.run(network, proto_info)
        for p in processes:
            p.join()
        return True

    def run_flow(self, flow, network: INetwork, start_barrier):
        start_barrier.wait()
        start_delay = random.uniform(self.min_start, self.max_start)
        duration = random.uniform(self.min_duration, self.max_duration)
        if start_delay + duration > self.max_interval:
            duration = self.max_interval - start_delay
        time.sleep(start_delay)
        client = network.get_hosts()[flow.client_host]
        server = network.get_hosts()[flow.server_host]
        server_ip = server.IP()
        logging.info(
            "Starting competition flow:  %s -> %s with delay %d, duration %d",
            client.name(), server.name(), start_delay, duration)
        server.cmd(f'iperf3 -s -p 5001 --logfile {self.result.record} &')
        res = client.popen(
            f'iperf3 -c {server_ip} -p 5001 -i 1 -t {int(duration)}').stdout.read().decode('utf-8')
        logging.info('iperf client output: %s', res)
        logging.info(
            "Finished competition flow:  %s -> %s", client.name(), server.name())

    def post_process(self):
        return True

    def pre_process(self):
        return True
