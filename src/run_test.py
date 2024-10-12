from math import log
import os
import sys
import logging
import platform
import multiprocessing
from multiprocessing import Manager
from matplotlib.pylab import f
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from interfaces.network import INetwork
from containernet.topology import ITopology
from containernet.linear_topology import LinearTopology
from containernet.containernet_network import ContainerizedNetwork
from containernet.config import (
    IConfig, NodeConfig, TopologyConfig)
from testsuites.test import (TestType, TestConfig)
from testsuites.test_iperf import IperfTest
from testsuites.test_ping import PingTest
from testsuites.test_rtt import RTTTest
from testsuites.test_sshping import SSHPingTest
from routing.static_routing import StaticRouting
from routing.olsr_routing import OLSRRouting
from routing.openr_routing import OpenrRouting
from protosuites.proto import (ProtoConfig, SupportedProto)
from protosuites.std_protocol import StdProtocol
from protosuites.cs_protocol import CSProtocol
from protosuites.bats.bats_btp import BTP
from protosuites.bats.bats_brtp import BRTP
from protosuites.bats.bats_brtp_proxy import BRTPProxy
from data_analyzer.analyzer import AnalyzerConfig
from data_analyzer.analyzer_factory import AnalyzerFactory
from tools.util import is_same_path

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
        for res in test_result['results']:
            result_files.append(res.record)
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


def build_network(node_config: NodeConfig, top: ITopology, route: str = "static_route"):
    """Build a container network from the yaml configuration file.

    Args:
        yaml_test_file_path (str): the path of the yaml configuration file

    Returns:
        ContainerizedNetwork: the container network object
    """
    route_strategy = StaticRouting()
    if route == "static_route":
        route_strategy = StaticRouting()
    if route == "olsr_route":
        route_strategy = OLSRRouting()
    elif route == "openr_route":
        route_strategy = OpenrRouting()
    return ContainerizedNetwork(node_config, top, route_strategy)


def handle_test_failure(test_name):
    logging.error("Test %s failed.", test_name)
    # create a regular file to indicate the test failure
    with open(f"/root/test.failed", 'w', encoding='utf-8') as f_failed:
        f_failed.write(f"{test_name}")


def handle_test_success():
    # create a regular file to indicate the test success
    with open(f"/root/test.success", 'w', encoding='utf-8') as f:
        f.write(f"test.success")


def perform_test_in_process(network, test_name, index, result_dict):
    logging.info(
        "########## Oasis process %d Performing the test for %s", index, test_name)
    is_success = network.perform_test()
    if is_success is False:
        handle_test_failure(test_name)
        logging.error(
            "########## Oasis process %d failed the test for %s", index, test_name)
        return
    result_dict[index] = network.get_test_results()
    logging.debug(
        "########## Oasis process %d finished the test for %s, results %s",
        index, test_name, result_dict[index])


def stop_networks(start, end, nets):
    for index in range(start, end):
        nets[index].stop()
        logging.info("########## Oasis stop the network %s.", index)


def reset_networks(proto_num, nets):
    for index in range(proto_num):
        nets[index].reset()
        logging.info("########## Oasis reset the network %s.", index)


if __name__ == '__main__':
    debug_log = 'True'
    if len(sys.argv) == 5:
        debug_log = sys.argv[4]
    if debug_log == 'True':
        setLogLevel('info')
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Debug mode is enabled.")
    else:
        setLogLevel('warning')
        logging.basicConfig(level=logging.INFO)
        logging.info("Debug mode is disabled.")
    logging.info("Platform: %s", platform.platform())
    logging.info("Python version: %s", platform.python_version())
    yaml_config_base_path = sys.argv[1]
    oasis_workspace = sys.argv[2]
    logging.info("Yaml config path: %s", yaml_config_base_path)
    logging.info("Oasis workspace: %s", oasis_workspace)
    # config_mapped_prefix can be `/root/config/` or `/root/src/config/`
    if is_same_path(yaml_config_base_path, f"{oasis_workspace}/src/config/"):
        # oasis workspace mapped to `/root/`
        logging.info("No config path mapping is needed.")
        config_mapped_prefix = '/root/src/config/'
    else:
        # oasis yaml config files mapped to `/root/config/`
        logging.info("Oasis yaml config files mapped to `/root/config/`.")
        config_mapped_prefix = '/root/config/'
    oasis_mapped_prefix = '/root/'
    logging.info(
        f"run_test.py: Base path of the oasis project: %s", oasis_workspace)
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
    linear_network = None
    cur_node_config = load_node_config(
        config_mapped_prefix, yaml_test_file_path)
    if cur_node_config.name == "":
        logging.error("Error: no containernet node config.")
        sys.exit(1)
    # mount the workspace
    cur_node_config.vols.append(f'{oasis_workspace}:{oasis_mapped_prefix}')
    if config_mapped_prefix == '/root/config/':
        cur_node_config.vols.append(
            f'{yaml_config_base_path}:{config_mapped_prefix}')
    target_proto_num = 0
    # load all cases
    networks = []
    all_tests = load_test(yaml_test_file_path, cur_selected_test)
    if all_tests is None:
        logging.error("Error: no test case found.")
        sys.exit(1)
    for test in all_tests:
        cur_test_name = test['name']
        # execution mode default is serial
        cur_execution_mode = test.get('execution_mode', 'serial')
        if cur_execution_mode not in supported_execution_mode:
            logging.warning("Error: unsupported execution mode.")
            continue
        org_name_prefix = cur_node_config.name_prefix
        # 1. load target protocols
        target_protocols = load_target_protocols_config(
            config_mapped_prefix, test)
        if target_protocols is None:
            logging.error("Error: no target protocols.")
            sys.exit(1)
        target_proto_num = len(
            target_protocols) if target_protocols is not None else 0
        if target_proto_num == 0:
            logging.error("Error: no target protocols.")
            sys.exit(1)
        if target_proto_num > len(alphabet):
            logging.error("Error: too many target protocols.")
            sys.exit(1)

        cur_topology = load_topology(config_mapped_prefix, test)
        for cur_top_index, cur_top_ins in enumerate(cur_topology):
            # 2. build the network for each target protocol
            if not is_parallel_execution(cur_execution_mode):
                # serial execution only needs one network
                target_proto_num = 1
                logging.info("########## Oasis execute the test %s in serial mode.",
                             cur_test_name)
            cur_net_num = len(networks)
            if cur_net_num != target_proto_num:
                # targets changed.
                if cur_net_num < target_proto_num:
                    for i in range(cur_net_num, target_proto_num):
                        if is_parallel_execution(cur_execution_mode):
                            logging.info(
                                "####################################################")
                            logging.info(
                                "########## Oasis Parallel Execution Mode. ##########")
                            logging.info(
                                "########## network instance %s             ##########", i)
                            logging.info(
                                "####################################################")
                            cur_node_config.name_prefix = f"{org_name_prefix}{alphabet[i]}"
                            cur_node_config.bind_port = False
                        network_ins = build_network(
                            cur_node_config, cur_top_ins, test['route'])
                        if network_ins is None:
                            logging.error("Error: failed to build network.")
                            continue
                        networks.append(network_ins)
                elif cur_net_num > target_proto_num:
                    # stop the extra networks
                    stop_networks(target_proto_num, cur_net_num, networks)
                    networks = networks[:target_proto_num]
            # 2.1 or reload networks if networks is already built
            for i in range(target_proto_num):
                if not networks[i].is_started():
                    networks[i].start()
                else:
                    # reload the already started network
                    networks[i].reload(cur_top_ins)
                logging.info("########## Oasis reload the network %s.", i)
            cur_top_description = networks[0].get_topology_description()
            logging.info(
                "######################################################")
            logging.info("########## Oasis traverse the topologies: [%d] \n %s.",
                         cur_top_index,
                         cur_top_description)
            logging.info(
                "######################################################")
            # 3. setup the test for each target protocol
            for i in range(target_proto_num):
                selected_protocols = []
                if is_parallel_execution(cur_execution_mode):
                    selected_protocols = [target_protocols[i]]
                else:
                    selected_protocols = target_protocols
                if setup_test(test, selected_protocols, networks[i]) is False:
                    logging.error("Error: failed to setup the test.")
                    stop_networks(0, target_proto_num, networks)
                    sys.exit(1)

            # 4. perform the test for each target protocol in parallel with different processes
            processes = []
            manager = Manager()
            process_shared_dict = manager.dict()
            for i in range(target_proto_num):
                p = multiprocessing.Process(target=perform_test_in_process,
                                            args=(networks[i],
                                                  cur_test_name,
                                                  i, process_shared_dict))
                processes.append(p)
                p.start()

            # 4.1 Wait for all processes to complete
            for i, p in enumerate(processes):
                p.join(timeout=600)
                if p.is_alive():
                    logging.error(f"Process %s for test %s is stuck.",
                                  i, cur_test_name)
                    p.terminate()
                    p.join()
                    logging.info(f"Process %s for test %s is terminated.",
                                 i, cur_test_name)
                else:
                    logging.info(f"Process %s for test %s is completed successfully.",
                                 i, cur_test_name)

            # 5. merge multiple test results into one dictionary
            merged_results = {}
            for i in range(target_proto_num):
                if i not in process_shared_dict:
                    logging.error(f"No results found for process %s.", i)
                    handle_test_failure(cur_test_name)
                    stop_networks(0, target_proto_num, networks)
                    sys.exit(1)
                for shared_test_type, shared_test_result in process_shared_dict[i].items():
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
                                       cur_top_description) is False:
                logging.error("Test %s results analysis not passed.",
                              cur_test_name)
                handle_test_failure(cur_test_name)
                stop_networks(0, target_proto_num, networks)
                sys.exit(1)

            # 5.2 move results(logs, diagrams) to "{cur_results_path}/{cur_top_index}"
            cur_results_path = merged_results[0]['results'][0].result_dir
            logging.info("cur_results_path %s",
                         cur_results_path)
            archive_dir = f"{cur_results_path}topology-{cur_top_index}"
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
            # 5.3 save cur_top_description
            with open(f"{archive_dir}/topology_description.txt", 'w', encoding='utf-8') as f:
                f.write(f"{cur_top_description}")

            # 6. reset the network then go to the next test case
            reset_networks(target_proto_num, networks)
            manager.shutdown()
        # > for cur_top_ins in cur_topology:
    # > for test in all_tests
    handle_test_success()
    stop_networks(0, target_proto_num, networks)
    sys.exit(0)
