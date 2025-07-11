import os
import sys
import copy
import logging
import multiprocessing
from multiprocessing import Manager
import yaml

from interfaces.network_mgr import INetworkManager
from interfaces.network import INetwork
from core.topology import ITopology
from testsuites.test import (
    ITestSuite, TestType, TestConfig, test_type_str_mapping)
from testsuites.test_iperf import IperfTest
from testsuites.test_iperf_bats import IperfBatsTest
from testsuites.test_ping import PingTest
from testsuites.test_rtt import RTTTest
from testsuites.test_scp import ScpTest
from testsuites.test_regular import RegularTest
from testsuites.test_competition import (
    FlowCompetitionTest, FlowCompetitionConfig, FlowParameter)
from protosuites.proto import (ProtoConfig, SupportedProto, ProtoRole)
from protosuites.std_protocol import StdProtocol
from protosuites.cs_protocol import CSProtocol
from protosuites.noop_protocol import (
    NoOpProtocol, is_next_protocol, is_no_op_protocol)
from protosuites.bats.bats_btp import BTP
from protosuites.bats.bats_brtp import BRTP
from protosuites.bats.bats_brtp_proxy import BRTPProxy
from data_analyzer.analyzer import AnalyzerConfig
from data_analyzer.analyzer_factory import AnalyzerFactory
from var.global_var import g_root_path

supported_execution_mode = ["serial", "parallel"]


def is_parallel_execution(execution_mode: str):
    return execution_mode == "parallel"


def add_all_competition_flow_logs(test_results, log_path):
    # list all the logs files which match the pattern under folder log_path
    if not os.path.exists(log_path):
        logging.error("Log path %s does not exist.", log_path)
        return
    for file in os.listdir(log_path):
        if 'FlowCompetitionTest' in file and file.endswith('.log'):
            full_path = os.path.join(log_path, file)
            logging.info("Adding competition flow log: %s", full_path)
            test_results.append(full_path)


def diagnostic_test_results(test_results, top_des):
    if len(test_results) == 0:
        logging.error("Error: no test results. %s", top_des)
        return False
    for test_type, test_result in test_results.items():
        logging.debug(
            "########################## Oasis Analyzing Test Results %s %s"
            "##########################", test_type, test_result)
        test_config = test_result['config']
        result_files = []
        logging.info("############ test_result['results'] len %s %s", len(
            test_result['results']), test_result)
        for result in test_result['results']:
            if result.is_competition_test:
                add_all_competition_flow_logs(result_files, result.result_dir)
            result_files.append(result.record)
        # analyze those results files according to the test type
        analyzer_name = test_type_str_mapping[test_type]
        config = AnalyzerConfig(
            input=result_files,
            output=f"{test_result['results'][0].result_dir}",
            subtitle=top_des)
        if test_type == TestType.throughput:
            if 'bats_iperf' in test_config.name:
                test_config.packet_type = 'bats'
            if test_config.packet_type == 'tcp':
                config.output = f"{test_result['results'][0].result_dir}iperf3_throughput.svg"
            else:
                config.output = f"{test_result['results'][0].result_dir}iperf3_{test_config.packet_type}_statistics.svg"
            config.data_type = f"{test_config.packet_type}"
        if test_type == TestType.rtt:
            if test_config.packet_count == 1:
                analyzer_name = "first_rtt"
                config.output = f"{test_result['results'][0].result_dir}first_rtt.svg"
        analyzer = AnalyzerFactory.get_analyzer(analyzer_name, config)
        analyzer.visualize()
        if analyzer.analyze() is False:
            logging.error(
                "Test %s failed at %s test", test_config.name, analyzer_name)
            return False
    return True


def load_test_tool(tool, test_name) -> ITestSuite:
    test_conf = TestConfig(
        name=tool['name'],
        test_name=test_name,
        interval=tool['interval'] if 'interval' in tool else 1.0,
        interval_num=tool['interval_num'] if 'interval_num' in tool else 10,
        parallel=tool['parallel'] if 'parallel' in tool else 1,
        packet_type=tool['packet_type'] if 'packet_type' in tool else 'tcp',
        bitrate=tool['bitrate'] if 'bitrate' in tool else 0,
        client_host=tool['client_host'], server_host=tool['server_host'],
        args=tool['args'] if 'args' in tool else '')
    if tool['name'] == 'bats_iperf':
        test_conf.test_type = TestType.throughput
        return IperfBatsTest(test_conf)
    if 'iperf' in tool['name']:
        test_conf.test_type = TestType.throughput
        return IperfTest(test_conf)
    if tool['name'] == 'ping':
        test_conf.test_type = TestType.latency
        return PingTest(test_conf)
    if tool['name'] == 'rtt':
        test_conf.packet_count = tool['packet_count']
        test_conf.packet_size = tool['packet_size']
        test_conf.test_type = TestType.rtt
        return RTTTest(test_conf)
    if tool['name'] == 'scp':
        test_conf.file_size = tool['file_size'] if 'file_size' in tool else 1
        test_conf.test_type = TestType.scp
        return ScpTest(test_conf)
    return RegularTest(test_conf)


def load_predefined_protocols(config_base_path):
    """
    Load predefined protocols from the yaml file.
    """
    try:
        with open(f'{config_base_path}/predefined.protocols.yaml', 'r', encoding='utf-8') as stream:
            yaml_content = yaml.safe_load(stream)
    except FileNotFoundError:
        logging.error(
            "YAML file '%s'/predefined.protocols.yaml not found.", config_base_path)
        return None
    except yaml.YAMLError as exc:
        logging.error("Error parsing YAML file: %s", exc)
        return None
    if not yaml_content or 'protocols' not in yaml_content:
        logging.error("No protocols found in the YAML file.")
        return None
    predefined_protocols = yaml_content['protocols']
    predefined_proto_conf_dict = {}
    for protocol in predefined_protocols:
        if 'protocols' not in protocol:
            predefined_proto_conf_dict[protocol['name']] = ProtoConfig(
                **protocol)
            predefined_proto_conf_dict[protocol['name']
                                       ].config_base_path = config_base_path
            logging.info("load predefined protocol: %s",
                         predefined_proto_conf_dict[protocol['name']])
            continue
        # iterate over the protocols
        predefined_proto_conf_dict[protocol['name']] = ProtoConfig(
            **protocol)
        predefined_proto_conf_dict[protocol['name']
                                   ].config_base_path = config_base_path
        predefined_proto_conf_dict[protocol['name']].protocols = []
        logging.info("load predefined protocol: %s",
                     predefined_proto_conf_dict[protocol['name']])
        for sub_proto in protocol['protocols']:
            predefined_proto_conf_dict[protocol['name']].protocols.append(
                ProtoConfig(**sub_proto))
            logging.info("load predefined sub-protocol: %s",
                         sub_proto)

        # save the config_base_path for sub-protocol
        for sub_proto in predefined_proto_conf_dict[protocol['name']].protocols:
            sub_proto.config_base_path = config_base_path
    return predefined_proto_conf_dict


def load_target_protocols_config(config_base_path, test_case_yaml):
    """
        read target protocols from the test case yaml,
        And convert them into a list of `ProtoConfig`.
    """
    predefined = load_predefined_protocols(config_base_path)
    if predefined is None:
        logging.error("Error: no predefined protocols.")
        return None
    target_protocols_yaml = test_case_yaml['target_protocols']
    logging.info("target_protocols_yaml: %s", target_protocols_yaml)
    if target_protocols_yaml is None:
        logging.error("Error: target_protocols is None.")
        return None
    loaded_target_protocols = []
    if all(isinstance(protocol, str) for protocol in target_protocols_yaml):
        # ['btp', 'brtp', 'tcp']
        logging.debug("target_protocols is a list of strings.")
        loaded_target_protocols = [predefined[protocol]
                                   for protocol in target_protocols_yaml if protocol in predefined]
        if 'tcp' in target_protocols_yaml:
            loaded_target_protocols.append(ProtoConfig(
                name='tcp', type='distributed',))
        logging.debug("loaded protocol config: %s", loaded_target_protocols)
        return loaded_target_protocols
    if all(isinstance(protocol, dict) for protocol in target_protocols_yaml):
        logging.info("target_protocols is a list of dictionaries.")
        for protocol in target_protocols_yaml:
            if protocol['name'] not in SupportedProto:
                logging.error(
                    f"Error: unsupported protocol %s", protocol['name'])
                continue
            if 'protocols' not in protocol:
                loaded_target_protocols.append(ProtoConfig(**protocol))
            else:
                # iterate over the protocols
                local_proto_conf = ProtoConfig(
                    **protocol)
                local_proto_conf.protocols = []
                for sub_proto in protocol['protocols']:
                    local_proto_conf.protocols.append(
                        ProtoConfig(**sub_proto))
                    logging.info("load sub-protocol: %s",
                                 sub_proto)
                loaded_target_protocols.append(local_proto_conf)
        logging.debug("loaded protocol config: %s", loaded_target_protocols)
        return loaded_target_protocols
    logging.error("Error: unsupported target_protocols format.")
    return None


def setup_test(test_case_yaml, internal_target_protocols, network: INetwork):
    """setup the test case configuration.
    """
    # read the strategy matrix
    test_case_name = test_case_yaml['name']
    competition_flows = test_case_yaml.get('competition_flows', None)
    test_tools = test_case_yaml['test_tools']
    for proto_config in internal_target_protocols:
        proto_config.test_name = test_case_name
        logging.info("Added %s protocol, version %s.",
                     proto_config.name, proto_config.version)
        if proto_config.name not in ('brtp', 'btp', 'udp'):
            if any(tool.get('packet_type') == 'udp' for tool in test_tools.values()):
                logging.error(
                    "Error: iperf udp only works with protocol btp, brtp. but target protocol is %s",
                    proto_config.name)
                return False
        if is_next_protocol(proto_config.name):
            if 'bats_iperf' not in test_tools:
                logging.error(
                    "Error: bats_iperf test is required for next protocol %s", proto_config.name)
                return False
        if proto_config.type == 'distributed':
            if 'brtp_proxy' in proto_config.name:
                network.add_protocol_suite(BRTPProxy(proto_config))
                continue
            if 'brtp' in proto_config.name:
                network.add_protocol_suite(BRTP(proto_config))
                continue
            if 'btp' in proto_config.name:
                network.add_protocol_suite(BTP(proto_config))
                continue
            if is_no_op_protocol(proto_config.name):
                network.add_protocol_suite(NoOpProtocol(proto_config))
                continue
            network.add_protocol_suite(StdProtocol(proto_config))
            logging.warning("apply StdProtocol for %s protocol",
                            proto_config.name)
            continue
        if proto_config.type == 'none_distributed':
            sub_proto_num = len(
                proto_config.protocols) if proto_config.protocols else 0
            if sub_proto_num not in (2, 0):
                logging.error(
                    "Error: none distributed protocol invalid setup.")
                continue
            if sub_proto_num == 0:
                # copy the proto_config
                client_conf = copy.deepcopy(proto_config)
                server_conf = copy.deepcopy(proto_config)
                client_conf.name = f"{proto_config.name}_client"
                server_conf.name = f"{proto_config.name}_server"
            else:
                client_conf = proto_config.protocols[0]
                server_conf = proto_config.protocols[1]
            client_conf.port = proto_config.port
            server_conf.port = proto_config.port
            # by default, client-server hosts are [0, -1]
            hosts = network.get_hosts()
            if hosts is not None:
                proto_config.hosts = [0, len(hosts) - 1]
            else:
                proto_config.hosts = []
            proto_config.test_name = test_case_name
            client_conf.test_name = test_case_name
            server_conf.test_name = test_case_name
            client_proto_suite = StdProtocol(client_conf)
            server_proto_suite = StdProtocol(server_conf)
            if is_no_op_protocol(proto_config.name):
                logging.info("apply NoOpProtocol for %s protocol",
                             proto_config.name)
                client_proto_suite = NoOpProtocol(client_conf)
                server_proto_suite = NoOpProtocol(server_conf)
            if 'brtp_quic' in proto_config.name:
                client_proto_suite = BRTP(
                    client_conf, False, ProtoRole.client)
                server_proto_suite = BRTP(
                    server_conf, False, ProtoRole.server)
            # wrapper of client-server protocol
            cs = CSProtocol(config=proto_config,
                            client=client_proto_suite, server=server_proto_suite)
            network.add_protocol_suite(cs)
            continue
        logging.error("Error: unsupported protocol type %s.%s",
                      proto_config.type, proto_config.name)
    flow_competition_config = None
    if competition_flows:
        flow_params = [FlowParameter(**flow) for flow in competition_flows]
        flow_competition_config = FlowCompetitionConfig(
            competition_flow=flow_params)
    for name in test_tools.keys():
        test_tools[name]['name'] = name
        loaded_test_tool = load_test_tool(test_tools[name], test_case_name)
        if flow_competition_config and 'iperf' in loaded_test_tool.name():
            competition_test = FlowCompetitionTest(
                config=flow_competition_config,
                test=loaded_test_tool)
            network.add_test_suite(competition_test)
            logging.info("Added %s test with flow competition to %s.",
                         loaded_test_tool.name(), test_case_name)
            continue
        network.add_test_suite(loaded_test_tool)
        logging.info("Added %s test to %s.",
                     loaded_test_tool.name(), test_case_name)
    return True


class TestRunner:
    def __init__(self, test_yml_config, path, network_mgr: INetworkManager):
        self.test_yml_config = test_yml_config
        self.config_path = path
        self.target_protocols = None
        self.results_dict = None
        self.network_mgr = network_mgr
        self.net_num = 0
        self.top_description = ''
        self.is_ready_flag = False
        self._load_protocols()

    def init(self, node_config, topology: ITopology):
        # Test execution mode default is serial
        exec_mode = self.test_yml_config.get('execution_mode', 'serial')
        if exec_mode not in supported_execution_mode:
            logging.warning("Error: unsupported execution mode.")
            return
        if not is_parallel_execution(exec_mode):
            # serial execution only needs one network instance.
            required_network_ins = 1
        else:
            # @Note: About the parallel execution mode:
            # if parallel execution is enabled, oasis will create multiple
            # networks instances for each target protocol;
            # and each target protocol will be tested on each network instance.
            required_network_ins = self.target_protocol_num()
            if required_network_ins <= 1:
                logging.warning(
                    "parallel execution mode is enabled, but only one protocol target is specified")
        # 1.2 Build multiple network instances.
        self.is_ready_flag = self.network_mgr.build_networks(node_config,
                                                             topology,
                                                             required_network_ins,
                                                             self.test_yml_config['route'])

    def is_ready(self):
        return self.is_ready_flag

    def target_protocol_num(self):
        return len(self.target_protocols) if self.target_protocols is not None else 0

    def set_network_manager(self, mgr):
        if self.network_mgr is None:
            self.network_mgr = mgr

    def setup_tests(self):
        if self.network_mgr is None:
            logging.error("Error: no network manager.")
            return False
        networks = self.network_mgr.get_networks()
        if self.target_protocols is None:
            logging.error("Error: no target protocols.")
            return False
        pro_num = len(self.target_protocols)
        self.net_num = len(networks)
        if self.net_num == 0:
            logging.error("Error: no networks.")
            return False
        if pro_num == 0:
            logging.error("Error: no protocols.")
            return False
        # 3. setup the test for each target protocol
        for i in range(self.net_num):
            selected_protocols = []
            if self.net_num == pro_num:
                selected_protocols = [self.target_protocols[i]]
            else:
                selected_protocols = self.target_protocols
            if setup_test(self.test_yml_config,
                          selected_protocols,
                          networks[i]) is False:
                logging.error("Error: failed to setup the test.")
                return False
        return True

    def execute_tests(self):
        if self.network_mgr is None:
            logging.error("Error: no network manager.")
            return False
        if self.target_protocols is None:
            logging.error("Error: no target protocols.")
            return False
        self.network_mgr.start_networks()
        networks = self.network_mgr.get_networks()
        self.top_description = self.network_mgr.get_top_description()
        if self.net_num == 0:
            logging.error("Error: no networks.")
            return False
        process_manager = Manager()
        process_shared_dict = process_manager.dict()
        processes = []
        test_name = self.test_yml_config['name']
        # 4. perform the test for each target protocol in parallel with different processes
        for i in range(self.net_num):
            p = multiprocessing.Process(target=self._perform_test_in_process,
                                        args=(networks[i],
                                              test_name, process_shared_dict))
            processes.append(p)
            p.start()

        # 4.1 Wait for all processes to complete
        for i, p in enumerate(processes):
            max_wait_time = self.__get_test_time()
            logging.info(
                "########################## Oasis process execute ########################## ")
            logging.info(
                "Wait for process %s for test %s to complete in %s seconds", i, test_name, max_wait_time)
            p.join(timeout=max_wait_time)
            if p.is_alive():
                logging.error(f"Process %s for test %s is stuck.",
                              i, test_name)
                p.terminate()
                p.join()
                logging.info(f"Process %s for test %s is terminated.",
                             i, test_name)
            else:
                if i in process_shared_dict and isinstance(process_shared_dict[i], dict) \
                        and process_shared_dict[i].get("error"):
                    logging.error(
                        f"Process %d for test %s failed", i, test_name)
                else:
                    logging.info(f"Process %s for test %s is completed successfully.",
                                 i, test_name)

        # save results from different process.
        self.results_dict = copy.deepcopy(process_shared_dict)
        if process_manager:
            process_manager.shutdown()
            process_manager = None
            process_shared_dict = None
            processes = []
        self.network_mgr.reset_networks()
        return True

    def handle_test_results(self, top_index):
        # 5. merge multiple test results into one dictionary
        if self.results_dict is None:
            logging.error("Process shared dict is None.")
            return False
        test_name = self.test_yml_config['name']
        merged_results = {}
        for i in range(self.net_num):
            if i not in self.results_dict:
                logging.error(f"No results found for process %s.", i)
                return False
            if self.results_dict[i].get("error"):
                logging.error(
                    f"Process %d failed with error: %s", i, self.results_dict[i]['error'])
                return False
            for shared_test_type, shared_test_result in self.results_dict[i].items():
                if shared_test_type not in merged_results:
                    merged_results[shared_test_type] = {
                        'results': [],
                        'config': shared_test_result['config']
                    }
                merged_results[shared_test_type]['results'].extend(
                    shared_test_result['results'])
        logging.info(
            "########## Oasis merge parallel test results. %s", merged_results)
        allow_failure = self.test_yml_config.get('allow_failure', False)
        diag_suc = diagnostic_test_results(
            merged_results, self.top_description)
        # 5.1 diagnostic the test results
        if not diag_suc and not allow_failure:
            logging.error("Test %s results analysis not passed.",
                          test_name)
            return False
        if not diag_suc and allow_failure:
            logging.warning(
                "Test %s results analysis not passed, and failure is ignored.", test_name)
        # 5.2 move results(logs, diagrams) to "{cur_results_path}/{top_index}"
        cur_results_path = f"{g_root_path}test_results/{test_name}/"
        archive_dir = f"{cur_results_path}topology-{top_index}"
        logging.info("cur_results_path %s, archive_dir %s",
                     cur_results_path, archive_dir)
        if not os.path.exists(archive_dir):
            logging.info("Create archive directory %s", archive_dir)
            os.makedirs(archive_dir)
        # move all files and folders to the archive directory except folder which start with "topology-*"
        for root, dirs, files in os.walk(cur_results_path):
            if root != cur_results_path:
                # no iteration
                continue
            for dir_name in dirs:
                if dir_name.startswith("topology-"):
                    continue
                os.system(f"mv {root}/{dir_name} {archive_dir}")
                logging.info("Move %s to %s", dir_name, archive_dir)
            for file_name in files:
                os.system(f"mv {root}/{file_name} {archive_dir}")
                logging.info("Move %s to %s", file_name, archive_dir)
        # 5.3 save top_description
        with open(f"{archive_dir}/topology_description.txt", 'w', encoding='utf-8') as f:
            f.write(f"{self.top_description}")
            logging.debug("Save topology description to %s",
                          f"{archive_dir}/topology_description.txt")
        return True

    def cleanup(self):
        # 6. clean up the network instance
        if self.network_mgr:
            self.network_mgr.stop_networks()
        return True

    def _load_protocols(self):
        # 1. load target protocols
        logging.info("########################## Oasis Loading Protocols "
                     "##########################")
        self.target_protocols = load_target_protocols_config(
            self.config_path, self.test_yml_config)
        if self.target_protocols is None:
            logging.error("Error: no target protocols.")
            return False
        proto_num = len(
            self.target_protocols) if self.target_protocols is not None else 0
        if proto_num == 0:
            logging.error("Error: no target protocols.")
            return False
        return True

    def _perform_test_in_process(self, network, test_name, result_dict):
        """Execute the test in a separate process,
            then store the results in the shared dictionary.
        """
        id = network.get_id()
        logging.info(
            "########## Oasis process %d Performing the test for %s", id, test_name)
        success = network.perform_test()
        if not success:
            result_dict[id] = {"error": "perform_test_failed"}
        else:
            result_dict[id] = network.get_test_results()
            logging.info("Process %s results: %s", id, result_dict[id])

    def handle_failure(self):
        self.cleanup()
        test_name = self.test_yml_config['name']
        logging.error("Test %s failed.", test_name)
        # create a regular file to indicate the test failure
        with open(f"{g_root_path}test.failed", 'w', encoding='utf-8') as f_failed:
            f_failed.write(f"{test_name}")
        sys.exit(1)

    def __get_test_time(self):
        test_tools = self.test_yml_config['test_tools']
        execution_mode = self.test_yml_config.get(
            'execution_mode', 'serial')
        proto_num = len(
            self.target_protocols) if self.target_protocols is not None else 0
        max_test_time = 0
        sum_test_time = 0
        for tool in test_tools.values():
            # interval or interval_num is not set, use default value 1
            interval = tool.get('interval', 1)
            interval_num = tool.get('interval_num', 10)
            max_test_time = max(max_test_time, interval * interval_num)
            sum_test_time += interval * interval_num
        if execution_mode == 'serial':
            #  additional "proto_num * 15" is for initialization and cleanup
            return sum_test_time * proto_num + proto_num * 30
        return max_test_time * proto_num + proto_num * 30
