import os
import sys
import argparse
import logging

from containernet.containernet import (
    NestedContainernet, load_nested_config)

""" ################# USAGE OF THE SCRIPT ##########################
  start.py is used to initialize the nested containernet environment, 
and inside the nested containernet, it will execute the test cases 
through the run_test.py script.
"""


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
                        dest='containernet',
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


def build_nested_env(config_file, containernet_name, workspace):
    # join cur_workspace with nested_config_file
    absolute_path_of_config_file = os.path.join(
        workspace + "/", config_file)
    nested_config = load_nested_config(
        absolute_path_of_config_file, containernet_name)
    if nested_config is None:
        logging.info(
            f"Error: %s is not in the nested config file.", containernet_name)
        sys.exit(1)
    test_name = "default "
    # execute the test cases on nested containernet
    return NestedContainernet(
        nested_config, workspace, test_name)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    local_parser = parse_args()
    ns, args = local_parser.parse_known_args()
    cur_config_yaml_file_path = ns.tests_config_file
    nested_config_file = ns.nested_config_file
    nested_containernet = ns.containernet
    cur_workspace = ns.workspace

    if not os.path.exists(f'{cur_workspace}/{cur_config_yaml_file_path}'):
        logging.info(f"Error: %s does not exist.", {
                     cur_workspace}/{cur_config_yaml_file_path})
        sys.exit(1)
    nested_env = build_nested_env(
        nested_config_file, nested_containernet, cur_workspace)
    nested_env.start()
    nested_env.patch()
    nested_env.execute(
        f"python3 src/run_test.py {cur_workspace} "
        f"{cur_config_yaml_file_path}")
    nested_env.stop()
