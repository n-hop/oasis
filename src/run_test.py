from typing import Tuple
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
    IConfig, NodeConfig, TopologyConfig, supported_config_keys)
from testsuites.test import (TestType, TestConfig)
from testsuites.test_iperf import IperfTest
from testsuites.test_ping import PingTest
from routing.static_routing import StaticRouting
from protosuites.proto import (ProtoConfig, SupportedProto, SupportedBATSProto)
from protosuites.tcp_protocol import TCPProtocol
from protosuites.kcp_protocol import KCPProtocol
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
            test_cases = yaml_content["test"]
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


def setup_test(test_case_yaml, network: INetwork):
    """setup the test case configuration.
    """
    # read the strategy matrix
    strategy = test_case_yaml['strategy']
    matrix = strategy['matrix']
    target_protocols = matrix['target_protocols']
    bats_protocol_version = matrix['bats_protocol_version']
    for proto in target_protocols:
        if proto not in SupportedProto:
            logging.error(
                f"Error: unsupported protocol %s", proto)
            continue
        if proto in SupportedBATSProto:
            # combine the protocol with the its version
            for version in bats_protocol_version:
                bats_proto_config = ProtoConfig(
                    protocol_path="/root/bats/bats_protocol",
                    protocol_args="--daemon_enabled=true",
                    protocol_version=version)
                # map `proto` into python object BTP, BRTP, BRTPProxy
                bats = None
                if proto == 'btp':
                    bats = BTP(bats_proto_config)
                    logging.info("Added bats BTP protocol.")
                elif proto == 'brtp':
                    bats_proto_config.protocol_args += " --tun_protocol=BRTP"
                    bats = BRTP(bats_proto_config)
                    logging.info("Added bats BRTP protocol.")
                elif proto == 'brtp_proxy':
                    bats = BRTPProxy(bats_proto_config)
                    logging.info("Added bats BRTP proxy protocol.")
                network.add_protocol_suite(bats)
        elif proto == 'tcp':
            config = ProtoConfig()
            network.add_protocol_suite(TCPProtocol(config))
            logging.info("Added TCP protocol.")
        elif proto == 'kcp':
            kcp_client_cfg = ProtoConfig(
                protocol_path="/root/kcp/client_linux_amd64",
                protocol_args="client",
                protocol_version="latest")
            kcp_server_cfg = ProtoConfig(
                protocol_path="/root/kcp/server_linux_amd64",
                protocol_args= "server",
                protocol_version="latest")
            cs = CSProtocol(KCPProtocol(kcp_client_cfg), KCPProtocol(kcp_server_cfg))
            network.add_protocol_suite(cs)
            logging.info("Added KCP protocol.")
        else:
            logging.error(
                f"Error: not implemented protocol %s", proto)
    # read test_tools
    test_tools = test_case_yaml['test_tools']
    for tool in test_tools:
        if tool['name'] == 'iperf':
            iperf_test_conf = TestConfig(
                interval=tool['interval'], interval_num=tool['interval_num'],
                test_type=TestType.throughput, log_file="/root/iperf_test.log",
                client_host=tool['client_host'], server_host=tool['server_host'])
            network.add_test_suite(IperfTest(iperf_test_conf))
            logging.info("Added iperf test.")
        elif tool['name'] == 'ping':
            ping_test_conf = TestConfig(
                interval=tool['interval'], interval_num=tool['interval_num'],
                test_type=TestType.latency, log_file="/root/ping_test.log",
                client_host=tool['client_host'], server_host=tool['server_host'])
            network.add_test_suite(PingTest(ping_test_conf))
            logging.info("Added ping test.")
        else:
            logging.error(
                f"Error: unsupported test tool %s", tool['name'])
    # read route
    route = test_case_yaml['route']
    logging.info("Route: %s", route)


def load_net_config(test_case_yaml) -> Tuple[NodeConfig, TopologyConfig]:
    """Load network related configuration from the yaml file.
    """
    configs = []
    for key in supported_config_keys:
        if key not in test_case_yaml:
            logging.error(
                f"Error: missing key %s in the test case yaml.",
                key)
            return None, None
        local_yaml = test_case_yaml[key]
        logging.info(f"Test: local_yaml %s",
                     local_yaml)
        if local_yaml is None:
            logging.error(f"Error: content of %s is None.", key)
            return None, None
        loaded_conf = IConfig.load_yaml_config(
            local_yaml, key)
        if loaded_conf is None:
            logging.error("Error: loaded_conf of %s is None.", key)
            return None, None
        configs.append(loaded_conf)
    return configs[0], configs[1]


def build_topology(top_config: TopologyConfig):
    built_net_top = None
    if top_config.topology_type == "linear":
        built_net_top = LinearTopology(top_config)
    else:
        logging.error("Error: unsupported topology type.")
        return None
    return built_net_top


def build_network(node_config: NodeConfig, top_config: TopologyConfig):
    """Build a container network from the yaml configuration file.

    Args:
        yaml_file_path (str): the path of the yaml configuration file

    Returns:
        ContainerizedNetwork: the container network object
    """
    net_top = build_topology(top_config)
    return ContainerizedNetwork(node_config, net_top, StaticRouting())


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
    all_tests = load_test(yaml_file_path)
    for test in all_tests:
        cur_node_config, cur_top_config = load_net_config(test)
        # mount the workspace
        cur_node_config.node_vols.append(f'{cur_workspace}:{mapped_workspace}')
        if linear_network is None:
            linear_network = build_network(cur_node_config, cur_top_config)
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
