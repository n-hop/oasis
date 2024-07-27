import os
import sys
import argparse
import logging
import yaml

from mininet.log import setLogLevel
from containernet.linear_net import LinearNet
from containernet.containernet import PairNet
from containernet.node_config import NodeConfig
from containernet.nested_containernet import (
    NestedContainernet, NestedConfig, load_nested_config)


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-n',
                        help='YAML configuration file for nested containernet',
                        dest='nested_config_file',
                        type=str,
                        default="")
    parser.add_argument('--containernet',
                        help='nested containernet name in the YAML file',
                        dest='nested_containernet',
                        type=str,
                        default="nuc_sz")
    parser.add_argument('-t',
                        help='YAML file for the test case to be executed',
                        dest='tests_config_file',
                        type=str,
                        default="")
    parser.add_argument('-w',
                        help='workspace directory',
                        dest='workspace',
                        type=str,
                        default="")
    return parser


def build_nested_env(nested_config_file, nested_containernet, workspace):
    nested_config = load_nested_config(
        nested_config_file, nested_containernet)
    if nested_config is None:
        logging.info(
            f"Error: {nested_containernet} is not in the nested config file.")
        sys.exit(1)
    test_name = "default "
    # execute the test cases on nested containernet
    return NestedContainernet(
        nested_config, workspace, test_name)


def build_network(yaml_file_path):
    # TODO(.): chain of responsibility
    with open(yaml_file_path, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    net = LinearNet(yaml_content['topology'])
    config = NodeConfig(** yaml_content['node_config'])
    return PairNet(config, net)


if __name__ == '__main__':
    # set log level
    setLogLevel('info')
    logging.basicConfig(level=logging.INFO)

    local_parser = parse_args()
    ns, args = local_parser.parse_known_args()
    cur_config_yaml_file_path = ns.tests_config_file
    nested_config_file = ns.nested_config_file
    nested_containernet = ns.nested_containernet
    cur_workspace = ns.workspace

    if not os.path.exists(cur_config_yaml_file_path):
        logging.info(f"Error: %s does not exist.", cur_config_yaml_file_path)
        sys.exit(1)
    nested_env = build_nested_env(
        nested_config_file, nested_containernet, cur_workspace)
    nested_env.start()
    nested_env.execute("")
    # self.docker_cmd = f"python3 execute_test.py {case_config_yaml_file_path} {self.workspace}"
    # pair_net = build_network(cur_config_yaml_file_path)
    nested_env.stop()
