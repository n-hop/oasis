import os
import sys
import copy
import logging
import platform
import multiprocessing
from multiprocessing import Manager
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from interfaces.network import INetwork
from containernet.topology import ITopology
from containernet.linear_topology import LinearTopology
from containernet.config import (
    IConfig, NodeConfig, TopologyConfig)
from testsuites.test import (TestType, TestConfig)
from testsuites.test_iperf import IperfTest
from testsuites.test_ping import PingTest
from testsuites.test_rtt import RTTTest
from testsuites.test_sshping import SSHPingTest
from testsuites.test_scp import ScpTest
from protosuites.proto import (ProtoConfig, SupportedProto)
from protosuites.std_protocol import StdProtocol
from protosuites.cs_protocol import CSProtocol
from protosuites.bats.bats_btp import BTP
from protosuites.bats.bats_brtp import BRTP
from protosuites.bats.bats_brtp_proxy import BRTPProxy
from data_analyzer.analyzer import AnalyzerConfig
from data_analyzer.analyzer_factory import AnalyzerFactory
from tools.util import (is_same_path, is_base_path)
from var.global_var import g_root_path
from core.network_mgr import NetworkManager

supported_execution_mode = ["serial", "parallel"]
# alphabet table
alphabet = ['h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't']


def is_parallel_execution(execution_mode: str):
    return execution_mode == "parallel"


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
        logging.debug("test_result['results'] len %s", len(
            test_result['results']))
        for result in test_result['results']:
            result_files.append(result.record)
        # analyze those results files according to the test type
        if test_type == TestType.throughput:
            output_svg = ""
            if test_config.packet_type == 'tcp':
                output_svg = f"{test_result['results'][0].result_dir}iperf3_throughput.svg"
            else:
                output_svg = f"{test_result['results'][0].result_dir}iperf3_udp_statistics.svg"
            config = AnalyzerConfig(
                input=result_files,
                output=f"{output_svg}",
                data_type=f"{test_config.packet_type}",
                subtitle=top_des)
            analyzer = AnalyzerFactory.get_analyzer("iperf3", config)
            if analyzer.analyze() is False:
                logging.error(
                    "Test %s failed at throughput test", test_config.name)
                return False
            analyzer.visualize()
        if test_type == TestType.rtt:
            if test_config.packet_count > 1:
                config = AnalyzerConfig(
                    input=result_files,
                    output=f"{test_result['results'][0].result_dir}",
                    subtitle=top_des)
                analyzer = AnalyzerFactory.get_analyzer("rtt", config)
                if analyzer.analyze() is False:
                    logging.error(
                        "Test %s failed at rtt test", test_config.name)
                    return False
                analyzer.visualize()
            if test_config.packet_count == 1:
                config = AnalyzerConfig(
                    input=result_files,
                    output=f"{test_result['results'][0].result_dir}first_rtt.svg",
                    subtitle=top_des)
                analyzer = AnalyzerFactory.get_analyzer(
                    "first_rtt", config)
                if analyzer.analyze() is False:
                    logging.error(
                        "Test %s failed at first_rtt test", test_config.name)
                    return False
                analyzer.visualize()
        if test_type == TestType.sshping:
            config = AnalyzerConfig(
                input=result_files,
                output=f"{test_result['results'][0].result_dir}",
                subtitle=top_des)
            analyzer = AnalyzerFactory.get_analyzer("sshping", config)
            if analyzer.analyze() is False:
                logging.error(
                    "Test %s failed at sshping test", test_config.name)
                return False
            analyzer.visualize()
        if test_type == TestType.scp:
            logging.error("scp test results: %s", result_files)
    return True


def load_test(test_yaml_file: str, test_name: str = "all"):
    """
        Load the test case configuration from a yaml file.
    """
    logging.info(
        "########################## Oasis Loading Tests "
        "##########################")
    # List of active cases.
    test_cases = None
    with open(test_yaml_file, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
            test_cases = yaml_content["tests"]
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    # ------------------------------------------------
    test_names = test_cases.keys()
    active_test_list = []
    if test_name in ("all", "All", "ALL"):
        test_name = ""
    for name in test_names:
        if test_name not in ("", name):
            logging.debug("Oasis skips the test case %s", name)
            continue
        test_cases[name]['name'] = name
        active_test_list.append(test_cases[name])
    for case in active_test_list.copy():
        # ignore the inactive case by "if: False"
        if "if" in case and not case["if"]:
            logging.info(
                f"case %s is disabled!", case['name'])
            active_test_list.remove(case)
        else:
            logging.info(
                f"case %s is enabled!", case['name'])
    if len(active_test_list) == 0:
        logging.info(f"No active test case in %s", test_yaml_file)
        return None
    return active_test_list


def add_test_to_network(network, tool, test_name):
    test_conf = TestConfig(
        name=test_name,
        interval=tool['interval'] if 'interval' in tool else 1.0,
        interval_num=tool['interval_num'] if 'interval_num' in tool else 10,
        packet_type=tool['packet_type'] if 'packet_type' in tool else 'tcp',
        bitrate=tool['bitrate'] if 'bitrate' in tool else 0,
        client_host=tool['client_host'], server_host=tool['server_host'])
    if tool['name'] == 'iperf':
        test_conf.test_type = TestType.throughput
        network.add_test_suite(IperfTest(test_conf))
        logging.info("Added iperf test to %s.", test_name)
    elif tool['name'] == 'ping':
        test_conf.test_type = TestType.latency
        network.add_test_suite(PingTest(test_conf))
        logging.info("Added ping test to %s.", test_name)
    elif tool['name'] == 'rtt':
        test_conf.packet_count = tool['packet_count']
        test_conf.packet_size = tool['packet_size']
        test_conf.test_type = TestType.rtt
        network.add_test_suite(RTTTest(test_conf))
        logging.info("Added rtt test to %s.", test_name)
    elif tool['name'] == 'sshping':
        test_conf.test_type = TestType.sshping
        network.add_test_suite(SSHPingTest(test_conf))
        logging.info("Added sshping test to %s.", test_name)
    elif tool['name'] == 'scp':
        test_conf.test_type = TestType.scp
        network.add_test_suite(ScpTest(test_conf))
        logging.info("Added scp test to %s.", test_name)
    else:
        logging.error(
            f"Error: unsupported test tool %s", tool['name'])


def load_predefined_protocols(config_base_path):
    """
    Load predefined protocols from the yaml file.
    """
    predefined_protocols = None
    with open(f'{config_base_path}/predefined.protocols.yaml', 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
            predefined_protocols = yaml_content['protocols']
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
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
    test_tools = test_case_yaml['test_tools']
    for proto_config in internal_target_protocols:
        proto_config.test_name = test_case_name
        logging.info("Added %s protocol, version %s.",
                     proto_config.name, proto_config.version)
        if proto_config.name not in ('brtp', 'btp'):
            if any(tool.get('packet_type') == 'udp' for tool in test_tools.values()):
                logging.error(
                    "Error: iperf udp only works with protocol btp, brtp. but target protocol is %s",
                    proto_config.name)
                return False
        if proto_config.type == 'distributed':
            # distributed protocol
            if 'brtp_proxy' in proto_config.name:
                network.add_protocol_suite(BRTPProxy(proto_config))
                continue
            if 'brtp' in proto_config.name:
                network.add_protocol_suite(BRTP(proto_config))
                continue
            if 'btp' in proto_config.name:
                network.add_protocol_suite(BTP(proto_config))
                continue
            if 'tcp' in proto_config.name:
                network.add_protocol_suite(StdProtocol(proto_config))
                continue
            logging.warning("Error: unsupported distributed protocol %s",
                            proto_config.name)
        if proto_config.type == 'none_distributed':
            # none distributed protocol
            if len(proto_config.protocols) != 2:
                logging.error(
                    "Error: none distributed protocol invalid setup.")
                continue
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
            # wrapper of client-server protocol
            cs = CSProtocol(config=proto_config,
                            client=StdProtocol(client_conf),
                            server=StdProtocol(server_conf))
            network.add_protocol_suite(cs)
            continue
        logging.error("Error: unsupported protocol type %s.%s",
                      proto_config.type, proto_config.name)
    for name in test_tools.keys():
        test_tools[name]['name'] = name
        add_test_to_network(network, test_tools[name], test_case_name)
    return True


def load_node_config(config_base_path, file_path) -> NodeConfig:
    """Load node related configuration from the yaml file.
    """
    node_config_yaml = None
    with open(file_path, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
            if yaml_content['containernet'] is None:
                logging.error("Error: no containernet node config.")
                return NodeConfig(name="", img="")
            node_config_yaml = yaml_content['containernet']["node_config"]
        except yaml.YAMLError as exc:
            logging.error(exc)
            return NodeConfig(name="", img="")
    if node_config_yaml is None:
        logging.error("Error: no containernet node config.")
        return NodeConfig(name="", img="")
    return IConfig.load_yaml_config(config_base_path,
                                    node_config_yaml, 'node_config')


def build_topology(top_config: TopologyConfig):
    built_net_top = None
    if top_config.topology_type == "linear":
        built_net_top = LinearTopology(top_config)
    else:
        logging.error("Error: unsupported topology type.")
        return None
    return built_net_top


def load_topology(config_base_path, test_case_yaml) -> ITopology:
    """Load network related configuration from the yaml file.
    """
    if 'topology' not in test_case_yaml:
        logging.error("Error: missing key topology in the test case yaml.")
        return None  # type: ignore
    local_yaml = test_case_yaml['topology']
    logging.info(f"Test: local_yaml %s",
                 local_yaml)
    if local_yaml is None:
        logging.error("Error: content of topology is None.")
        return None  # type: ignore
    loaded_conf = IConfig.load_yaml_config(config_base_path,
                                           local_yaml,
                                           'topology')
    if loaded_conf is None:
        logging.error("Error: loaded_conf of topology is None.")
        return None  # type: ignore
    return build_topology(loaded_conf)  # type: ignore


def handle_test_success():
    # create a regular file to indicate the test success
    with open(f"{g_root_path}test.success", 'w', encoding='utf-8') as f_success:
        f_success.write(f"test.success")


def perform_test_in_process(network, test_name, id, result_dict):
    """Execute the test in a separate process,
        then store the results in the shared dictionary.

    Args:
        id (int): The id of the process.
    """
    logging.info(
        "########## Oasis process %d Performing the test for %s", id, test_name)
    network.perform_test()
    result_dict[id] = network.get_test_results()
    logging.debug(
        "########## Oasis process %d finished the test for %s, results %s",
        id, test_name, result_dict[id])


class ContainerTestRunner:
    def __init__(self, test_yml_config, config_path, mgr: NetworkManager):
        self.test_yml_config = test_yml_config
        self.config_mapped_prefix = config_path
        self.target_protocols = None
        self.results_dict = None
        self.network_mgr = mgr
        self.net_num = 0
        self.top_description = ''
        self._load_protocols()

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
            p = multiprocessing.Process(target=perform_test_in_process,
                                        args=(networks[i],
                                              test_name,
                                              i, process_shared_dict))
            processes.append(p)
            p.start()

        # 4.1 Wait for all processes to complete
        for i, p in enumerate(processes):
            p.join(timeout=600)
            if p.is_alive():
                logging.error(f"Process %s for test %s is stuck.",
                              i, test_name)
                p.terminate()
                p.join()
                logging.info(f"Process %s for test %s is terminated.",
                             i, test_name)
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
        # 5.1 diagnostic the test results
        if diagnostic_test_results(merged_results,
                                   self.top_description) is False:
            logging.error("Test %s results analysis not passed.", test_name)
            return False

        # 5.2 move results(logs, diagrams) to "{cur_results_path}/{top_index}"
        cur_results_path = f"{g_root_path}test_results/{test_name}/"
        logging.info("cur_results_path %s", cur_results_path)
        archive_dir = f"{cur_results_path}topology-{top_index}"
        if not os.path.exists(archive_dir):
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
            for file_name in files:
                os.system(f"mv {root}/{file_name} {archive_dir}")
        # 5.3 save top_description
        with open(f"{archive_dir}/topology_description.txt", 'w', encoding='utf-8') as f:
            f.write(f"{self.top_description}")
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
            self.config_mapped_prefix, self.test_yml_config)
        if self.target_protocols is None:
            logging.error("Error: no target protocols.")
            return False
        proto_num = len(
            self.target_protocols) if self.target_protocols is not None else 0
        if proto_num == 0:
            logging.error("Error: no target protocols.")
            return False
        return True

    def handle_failure(self):
        self.cleanup()
        test_name = self.test_yml_config['name']
        logging.error("Test %s failed.", test_name)
        # create a regular file to indicate the test failure
        with open(f"{g_root_path}test.failed", 'w', encoding='utf-8') as f_failed:
            f_failed.write(f"{test_name}")
        sys.exit(1)


if __name__ == '__main__':
    debug_log = 'False'
    if len(sys.argv) == 5:
        debug_log = sys.argv[4]
    if debug_log == 'True':
        setLogLevel('info')
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Debug mode is enabled.")
    else:
        setLogLevel('info')
        logging.basicConfig(level=logging.INFO)
        logging.info("Debug mode is disabled.")
    logging.info("Platform: %s", platform.platform())
    logging.info("Python version: %s", platform.python_version())
    yaml_config_base_path = sys.argv[1]
    oasis_workspace = sys.argv[2]
    logging.info("Yaml config path: %s", yaml_config_base_path)
    logging.info("Oasis workspace: %s", oasis_workspace)
    # config_mapped_prefix can be `{g_root_path}config/` or `{g_root_path}src/config/`
    if is_same_path(yaml_config_base_path, f"{oasis_workspace}/src/config/"):
        # oasis workspace mapped to `{g_root_path}`
        logging.info("No config path mapping is needed.")
        config_mapped_prefix = f'{g_root_path}src/config/'
    else:
        # oasis yaml config files mapped to `{g_root_path}config/`
        config_mapped_prefix = f'{g_root_path}config/'
        logging.info(
            "Oasis yaml config files mapped to `%s`.", config_mapped_prefix)
    oasis_mapped_prefix = f'{g_root_path}'
    logging.info(
        f"run_test.py: Base path of the oasis project: %s", oasis_workspace)
    running_in_nested = False
    current_process_dir = os.getcwd()
    if is_base_path(current_process_dir, oasis_workspace):
        running_in_nested = False
        logging.info("##### running in a hosted environment.")
    else:
        running_in_nested = True
        logging.info("##### running in a nested environment.")
    cur_test_file = sys.argv[3]
    cur_selected_test = ""
    temp_list = cur_test_file.split(":")
    if len(temp_list) not in [1, 2]:
        logging.info("Error: invalid test case file format.")
        sys.exit(1)
    if len(temp_list) == 2:
        cur_test_file = temp_list[0]
        cur_selected_test = temp_list[1]
    yaml_test_file_path = f'{config_mapped_prefix}/{cur_test_file}'
    if not os.path.exists(yaml_test_file_path):
        logging.info(f"Error: %s does not exist.", yaml_test_file_path)
        sys.exit(1)

    cur_node_config = load_node_config(
        config_mapped_prefix, yaml_test_file_path)
    if cur_node_config.name == "":
        logging.error("Error: no containernet node config.")
        sys.exit(1)
    # mount the workspace
    cur_node_config.vols.append(f'{oasis_workspace}:{oasis_mapped_prefix}')
    if config_mapped_prefix == f'{g_root_path}config/':
        cur_node_config.vols.append(
            f'{yaml_config_base_path}:{config_mapped_prefix}')

    network_manager = NetworkManager()
    # 1. execute all the tests on all constructed networks
    all_networks = []
    all_tests = load_test(yaml_test_file_path, cur_selected_test)
    if all_tests is None:
        logging.error("Error: no test case found.")
        sys.exit(1)
    for test in all_tests:
        cur_topology = load_topology(config_mapped_prefix, test)
        # 1.1 The topology in one case can be composed of multiple topologies:
        #      Traverse all the topologies in the test case.
        for index, cur_top_ins in enumerate(cur_topology):
            test_runner = ContainerTestRunner(
                test, config_mapped_prefix, network_manager)
            # Test execution mode default is serial
            test_exec_mode = test.get('execution_mode', 'serial')
            if test_exec_mode not in supported_execution_mode:
                logging.warning("Error: unsupported execution mode.")
                continue
            if not is_parallel_execution(test_exec_mode):
                # serial execution only needs one network instance.
                required_network_ins = 1
            else:
                # @Note: About the parallel execution mode:
                # if parallel execution is enabled, oasis will create multiple
                # networks instances for each target protocol;
                # and each target protocol will be tested on each network instance.
                required_network_ins = test_runner.target_protocol_num()
            # 1.2 Build multiple network instances.
            logging.info("cur_top_ins %s", cur_top_ins)
            res = network_manager.build_networks(cur_node_config,
                                                 cur_top_ins,
                                                 required_network_ins,
                                                 test['route'])
            if res is False:
                continue
            # 1.3 Load test to the network instance
            res = test_runner.setup_tests()
            if res is False:
                test_runner.handle_failure()
            # 1.4 Execute the test on all network instances
            res = test_runner.execute_tests()
            if res is False:
                test_runner.handle_failure()
            # 1.5 Collect the test results, and analyze/diagnostic the results.
            res = test_runner.handle_test_results(index)
            if res is False:
                test_runner.handle_failure()
        # > for index, cur_top_ins in enumerate(cur_topology):
    # > for test in all_tests
    handle_test_success()
    sys.exit(0)
