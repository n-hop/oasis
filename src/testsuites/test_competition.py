import logging
import random
import time
import multiprocessing
from dataclasses import dataclass, field
from typing import Optional, List

from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite, test_type_str_mapping)


@dataclass
class FlowParameter:
    # valid format for `flow_type`: [protocol]-[cc] or [protocol]
    flow_type: str = field(default="tcp")
    client_host: int = field(default=0)
    server_host: int = field(default=1)
    delay: Optional[int] = field(default=None)
    # the flow will last for `duration` seconds.
    duration: Optional[int] = field(default=None)


@dataclass
class FlowCompetitionConfig:
    competition_flow: Optional[List[FlowParameter]] = field(default=None)


class FlowCompetitionTest(ITestSuite):
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

    def is_competition_test(self) -> bool:
        return True

    def _run_test(self, network: INetwork, proto_info: IProtoInfo):
        # multiprocessing to run competition flows
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
        if flow.delay is None or flow.duration is None:
            flow.delay = random.uniform(self.min_start, self.max_start)
            flow.duration = random.uniform(
                self.min_duration, self.max_duration)
            if flow.delay + flow.duration > self.max_interval:
                flow.duration = self.max_interval - flow.delay
        time.sleep(flow.delay)
        client = network.get_hosts()[flow.client_host]
        server = network.get_hosts()[flow.server_host]
        # format the flow_log_name
        flow_log_name = self.result.record
        if self.config.test_type is not None:
            flow_log_name = self.result.result_dir + \
                self.base_name + "_" + f"{self.__class__.__name__}_{self.config.name}_{self.config.packet_type}" \
                f"_{test_type_str_mapping[self.config.test_type]}" \
                f"_h{flow.client_host}_h{flow.server_host}.log"
        server_ip = server.IP()
        flow_meta_data = f'Competition flow: {client.name()} -> {server.name()} ' \
            f', delay:{flow.delay}, duration:{flow.duration}'
        cc = None
        protocol = flow.flow_type
        if '-' in flow.flow_type:
            parts = flow.flow_type.split("-")
            cc = parts[1] if len(parts) > 1 else None
            protocol = parts[0] if len(parts) > 1 else None
        flow_meta_data += f', protocol:{protocol}, cc:{cc}'
        server.cmd(f'echo \"{flow_meta_data}\" > {flow_log_name}')
        server.cmd(f'iperf3 -s -p 5001 --logfile {flow_log_name} &')
        logging.info(
            "Starting %s, log: %s", flow_meta_data, flow_log_name)
        if 'tcp' in flow.flow_type:
            if cc is None:
                res = client.popen(
                    f'iperf3 -c {server_ip} -p 5001 -i 1 -t {int(flow.duration)}').stdout.read().decode('utf-8')
            else:
                res = client.popen(
                    f'iperf3 -c {server_ip} -p 5001 -i 1 -t '
                    f'{int(flow.duration)} --congestion {cc}').stdout.read().decode('utf-8')
            logging.info('iperf client output: %s', res)
        if flow.flow_type in ('btp', 'brtp'):
            for intf in server.getIntfs():
                bats_iperf_server_cmd = f'bats_iperf -s -p 4000 -I {intf}' \
                    f' -l {flow_log_name} &'
                logging.info(
                    'bats_iperf server cmd: %s', bats_iperf_server_cmd)
                server.cmd(f'{bats_iperf_server_cmd}')
            args_from_proto = None
            if flow.flow_type == 'btp':
                args_from_proto = '-m 0'
            if flow.flow_type == 'brtp':
                args_from_proto = '-m 1'
            if args_from_proto is None:
                logging.error("unrecognized flow type %s", flow.flow_type)
            bats_iperf_client_cmd = f'bats_iperf -c {server_ip} {args_from_proto} -p 4000 ' \
                f' -i 1 -t {int(flow.duration)}'
            logging.info('bats_iperf client cmd: %s', bats_iperf_client_cmd)
            res = client.popen(
                f'{bats_iperf_client_cmd}').stdout.read().decode('utf-8')
        logging.info(
            "Finished competition flow: %s -> %s", client.name(), server.name())

    def post_process(self):
        # rewrite the self.result.record since the real target is the `self.test`.
        self.result.record = self.test.result.record
        return True

    def pre_process(self):
        return True
