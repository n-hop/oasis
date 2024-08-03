from typing import Tuple
import os
import sys
import logging
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from containernet.linear_topology import LinearTopology
from containernet.containerized_network import ContainerizedNetwork
from containernet.config import (
    IConfig, NodeConfig, TopologyConfig, supported_config_keys)
from testsuites.test import (TestType, TestConfig)
from testsuites.test_iperf import IperfTest
from testsuites.test_ping import PingTest


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


def load_config(test_case_yaml) -> Tuple[NodeConfig, TopologyConfig]:
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
    return ContainerizedNetwork(node_config, net_top)


if __name__ == '__main__':
    setLogLevel('info')
    logging.basicConfig(level=logging.INFO)

    # cur_workspace = sys.argv[1]
    cur_config_yaml_file_path = sys.argv[2]

    if not os.path.exists(cur_config_yaml_file_path):
        logging.info(f"Error: %s does not exist.", cur_config_yaml_file_path)
        sys.exit(1)
    linear_network = None
    all_tests = load_test(cur_config_yaml_file_path)
    for test in all_tests:
        cur_node_config, cur_top_config = load_config(test)
        if linear_network is None:
            linear_network = build_network(cur_node_config, cur_top_config)
            linear_network.start()
        else:
            local_net_top = build_topology(cur_top_config)
            if local_net_top is None:
                continue
            linear_network.reload(local_net_top)

        # add test suites
        iperf_test_conf = TestConfig(
            interval=1.0, interval_num=10, test_type=TestType.throughput)
        linear_network.add_test_suite(PingTest(iperf_test_conf))

        ping_test_conf = TestConfig(
            interval=1.0, interval_num=10, test_type=TestType.latency)
        linear_network.add_test_suite(IperfTest(ping_test_conf))

        # perform the test
        linear_network.perform_test()
        linear_network.reset_test_suites()

    linear_network.stop()
