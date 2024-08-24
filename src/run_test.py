import os
import sys
import logging
import platform
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from interfaces.network import INetwork
from containernet.linear_topology import LinearTopology
from containernet.containernet_network import ContainerizedNetwork
from containernet.config import (
    IConfig, NodeConfig, TopologyConfig)
from testsuites.test import (TestType, TestConfig)
from testsuites.test_iperf import IperfTest
from testsuites.test_ping import PingTest
from testsuites.test_rtt import RTTTest
from routing.static_routing import StaticRouting
from routing.olsr_routing import OLSRRouting
from routing.openr_routing import OpenrRouting
from protosuites.proto import (ProtoConfig, SupportedProto)
from protosuites.std_protocol import StdProtocol
from protosuites.cs_protocol import CSProtocol
from protosuites.bats.bats_btp import BTP
from protosuites.bats.bats_brtp import BRTP
from protosuites.bats.bats_brtp_proxy import BRTPProxy


def load_test(test_yaml_file: str):
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
    test_list = []
    for name in test_names:
        test_cases[name]['name'] = name
        test_list.append(test_cases[name])
    for case in test_list.copy():
        # ignore the inactive case by "if: False"
        if "if" in case and not case["if"]:
            logging.info(
                f"case %s is disabled!", case['name'])
            test_list.remove(case)
        else:
            logging.info(
                f"case %s is enabled!", case['name'])
    if len(test_list) == 0:
        logging.info(f"No active test case in %s", test_yaml_file)
        return None
    return test_list


def add_test_to_network(network, tool, test_name):
    test_conf = TestConfig(
        name=test_name,
        interval=tool['interval'], interval_num=tool['interval_num'] if 'interval_num' in tool else 10,
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
    else:
        logging.error(
            f"Error: unsupported test tool %s", tool['name'])


def load_predefined_protocols():
    """
    Load predefined protocols from the yaml file.
    """
    predefined_protocols = None
    with open('src/config/predefined.protocols.yaml', 'r', encoding='utf-8') as stream:
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
            logging.info("load predefined protocol: %s",
                         predefined_proto_conf_dict[protocol['name']])
            continue
        # iterate over the protocols
        predefined_proto_conf_dict[protocol['name']] = ProtoConfig(
            **protocol)
        predefined_proto_conf_dict[protocol['name']].protocols = []
        logging.info("load predefined protocol: %s",
                     predefined_proto_conf_dict[protocol['name']])
        for sub_proto in protocol['protocols']:
            predefined_proto_conf_dict[protocol['name']].protocols.append(
                ProtoConfig(**sub_proto))
            logging.info("load predefined sub-protocol: %s",
                         sub_proto)
    return predefined_proto_conf_dict


def load_target_protocols_config(test_case_yaml):
    """
        read target protocols from the test case yaml,
        And convert them into a list of `ProtoConfig`.
    """
    predefined = load_predefined_protocols()
    target_protocols_yaml = test_case_yaml['target_protocols']
    logging.info("target_protocols_yaml: %s", target_protocols_yaml)
    if target_protocols_yaml is None:
        logging.error("Error: target_protocols is None.")
        return None
    target_protocols = []
    if all(isinstance(protocol, str) for protocol in target_protocols_yaml):
        logging.debug("target_protocols is a list of strings.")
        target_protocols = [predefined[protocol]
                            for protocol in target_protocols_yaml if protocol in predefined]
        if 'tcp' in target_protocols_yaml:
            target_protocols.append(ProtoConfig(
                name='tcp', type='distributed',))
        logging.debug("loaded protocol config: %s", target_protocols)
        return target_protocols
    if all(isinstance(protocol, dict) for protocol in target_protocols_yaml):
        logging.info("target_protocols is a list of dictionaries.")
        for protocol in target_protocols_yaml:
            if protocol['name'] not in SupportedProto:
                logging.error(
                    f"Error: unsupported protocol %s", protocol['name'])
                continue
            if 'protocols' not in protocol:
                target_protocols.append(ProtoConfig(**protocol))
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
                target_protocols.append(local_proto_conf)
        logging.debug("loaded protocol config: %s", target_protocols)
        return target_protocols
    logging.error("Error: unsupported target_protocols format.")
    return None


def setup_test(test_case_yaml, network: INetwork):
    """setup the test case configuration.
    """
    # read the strategy matrix
    test_case_name = test_case_yaml['name']
    target_protocols = load_target_protocols_config(test_case_yaml)
    for proto_config in target_protocols:
        proto_config.test_name = test_case_name
        logging.info("Added %s protocol, version %s.",
                     proto_config.name, proto_config.version)
        if proto_config.type == 'distributed':
            # distributed protocol
            if proto_config.name == 'btp':
                network.add_protocol_suite(BTP(proto_config))
                continue
            if proto_config.name == 'brtp':
                network.add_protocol_suite(BRTP(proto_config))
                continue
            if proto_config.name == 'brtp_proxy':
                network.add_protocol_suite(BRTPProxy(proto_config))
                continue
            if 'tcp' in proto_config.name:
                network.add_protocol_suite(StdProtocol(proto_config))
                continue
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
            proto_config.hosts = [0, len(network.get_hosts()) - 1]
            proto_config.test_name = test_case_name
            client_conf.test_name = proto_config.test_case_name
            server_conf.test_name = proto_config.test_case_name
            # wrapper of client-server protocol
            cs = CSProtocol(config=proto_config,
                            client=StdProtocol(client_conf),
                            server=StdProtocol(server_conf))
            network.add_protocol_suite(cs)
            continue
        logging.error("Error: unsupported protocol type %s.%s",
                      proto_config.type, proto_config.name)
    # convert test_tools to test suites
    test_tools = test_case_yaml['test_tools']
    for name in test_tools.keys():
        test_tools[name]['name'] = name
        add_test_to_network(network, test_tools[name], test_case_name)


def load_node_config(file_path) -> NodeConfig:
    """Load node related configuration from the yaml file.
    """
    node_config_yaml = None
    with open(file_path, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
            if yaml_content['containernet'] is None:
                logging.error("Error: no containernet node config.")
                return None
            node_config_yaml = yaml_content['containernet']["node_config"]
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    if node_config_yaml is None:
        logging.error("Error: no containernet node config.")
        return None
    return IConfig.load_yaml_config(
        node_config_yaml, 'node_config')


def load_top_config(test_case_yaml) -> TopologyConfig:
    """Load network related configuration from the yaml file.
    """
    if 'topology' not in test_case_yaml:
        logging.error("Error: missing key topology in the test case yaml.")
        return None
    local_yaml = test_case_yaml['topology']
    logging.info(f"Test: local_yaml %s",
                 local_yaml)
    if local_yaml is None:
        logging.error("Error: content of topology is None.")
        return None
    loaded_conf = IConfig.load_yaml_config(
        local_yaml, 'topology')
    if loaded_conf is None:
        logging.error("Error: loaded_conf of topology is None.")
        return None
    return loaded_conf


def build_topology(top_config: TopologyConfig):
    built_net_top = None
    if top_config.topology_type == "linear":
        built_net_top = LinearTopology(top_config)
    else:
        logging.error("Error: unsupported topology type.")
        return None
    return built_net_top


def build_network(node_config: NodeConfig, top_config: TopologyConfig, route: str = None):
    """Build a container network from the yaml configuration file.

    Args:
        yaml_file_path (str): the path of the yaml configuration file

    Returns:
        ContainerizedNetwork: the container network object
    """
    net_top = build_topology(top_config)
    route_strategy = None
    if route is None or route == "static_route":
        route_strategy = StaticRouting()
    if route == "olsr_route":
        route_strategy = OLSRRouting()
    elif route == "openr_route":
        route_strategy = OpenrRouting()
    return ContainerizedNetwork(node_config, net_top, route_strategy)


if __name__ == '__main__':
    setLogLevel('info')
    logging.basicConfig(level=logging.INFO)
    logging.info("Platform: %s", platform.platform())
    logging.info("Python version: %s", platform.python_version())
    cur_workspace = sys.argv[1]
    mapped_workspace = '/root/'
    cur_config_yaml_file_path = sys.argv[2]
    yaml_file_path = f'{mapped_workspace}/{cur_config_yaml_file_path}'
    if not os.path.exists(yaml_file_path):
        logging.info(f"Error: %s does not exist.", yaml_file_path)
        sys.exit(1)
    linear_network = None
    cur_node_config = load_node_config(yaml_file_path)
    if cur_node_config is None:
        logging.error("Error: no containernet node config.")
        sys.exit(1)
    # mount the workspace
    cur_node_config.vols.append(f'{cur_workspace}:{mapped_workspace}')

    # load all cases
    all_tests = load_test(yaml_file_path)
    for test in all_tests:
        cur_top_config = load_top_config(test)
        if linear_network is None:
            linear_network = build_network(
                cur_node_config, cur_top_config, test['route'])
            linear_network.start()
        else:
            local_net_top = build_topology(cur_top_config)
            if local_net_top is None:
                continue
            linear_network.reload(local_net_top)

        # setup the test
        setup_test(test, linear_network)

        # perform the test
        linear_network.perform_test()
        linear_network.reset()

    linear_network.stop()
