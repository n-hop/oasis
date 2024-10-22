import os
import sys
import argparse
import logging

from var.global_var import g_root_path
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
    parser.add_argument('--containernet',
                        help='nested containernet name in the YAML file',
                        dest='containernet',
                        type=str,
                        default="")
    parser.add_argument('--testbed',
                        help='The name of testbed that will be used',
                        dest='testbed',
                        type=str,
                        default="")
    parser.add_argument('-t',
                        help='YAML file for the test case to be executed',
                        dest='tests_config_file',
                        type=str,
                        default="")
    parser.add_argument('-p',
                        help='base path of all the YAML files',
                        dest='yaml_base_path',
                        type=str,
                        default="")
    parser.add_argument('-d',
                        help='enable debug mode',
                        dest='debug_log',
                        type=str,
                        default='False')
    return parser


def build_nested_env(containernet_name, yaml_base_path_input, oasis_workspace_input):
    # join cur_workspace with nested_config_file
    absolute_path_of_config_file = os.path.join(
        yaml_base_path_input + "/", 'nested-containernet-config.yaml')
    if not os.path.exists(f'{absolute_path_of_config_file}'):
        logging.info(f"Error: %s does not exist.", {
                     absolute_path_of_config_file})
        return None
    nested_config = load_nested_config(
        absolute_path_of_config_file, containernet_name)
    if nested_config.image == "":
        logging.info(
            f"Error: %s is not in the nested config file.", containernet_name)
        sys.exit(1)
    test_name = "default "
    # execute the test cases on nested containernet
    return NestedContainernet(
        nested_config, yaml_base_path_input, oasis_workspace_input, test_name)


if __name__ == '__main__':
    local_parser = parse_args()
    ns, args = local_parser.parse_known_args()
    cur_test_yaml_file = ns.tests_config_file
    nested_containernet = ns.containernet
    baremetal_testbed = ns.testbed
    yaml_base_path = ns.yaml_base_path
    debug_log = ns.debug_log
    if debug_log == 'True':
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Debug mode is enabled.")
    else:
        logging.basicConfig(level=logging.INFO)
        logging.info("Debug mode is disabled.")
    current_process_dir = os.getcwd()
    logging.info(f"Current directory the process: %s", current_process_dir)

    base_path = os.path.dirname(os.path.abspath(__file__))
    oasis_workspace = os.path.dirname(base_path)
    logging.info(f"Base path of the oasis project: %s", oasis_workspace)
    if current_process_dir == oasis_workspace:
        logging.info("running in the workspace directory of oasis")
    else:
        logging.info("running outside the workspace directory of oasis")
    # ############### workspace dir and process dir ################
    # python source files are always started from the `oasis_workspace`
    # none py source files are always started from the `yaml_base_path`
    # ##############################################################
    # format of `cur_test_yaml_file`: folder1/folder2/test.yaml:test1
    temp_list = cur_test_yaml_file.split(":")
    if len(temp_list) not in [1, 2]:
        logging.info("Error: invalid test case file format.")
        sys.exit(1)
    if len(temp_list) == 2:
        cur_test_yaml_file = temp_list[0]
    # check whether yaml_base_path is an absolute path
    if not os.path.isabs(yaml_base_path):
        yaml_base_path = os.path.join(current_process_dir, yaml_base_path)
    test_case_file = os.path.join(
        yaml_base_path, cur_test_yaml_file)
    if not os.path.exists(f'{test_case_file}'):
        logging.info(f"Error: %s does not exist.", {test_case_file})
        sys.exit(1)
    # @Note: Oasis support test on containernet and bare metal testbed.
    #        For containernet, network is constructed and maintained by containernet.
    #        For bare metal testbed, network is constructed by real physical machines.
    if nested_containernet == "" and baremetal_testbed == "":
        logging.info(
            "Error: neither nested_containernet nor baremetal_testbed is provided.")
        sys.exit(1)
    if nested_containernet != "" and baremetal_testbed == "":
        logging.info("Oasis is running on nested containernet.")
    if nested_containernet == "" and baremetal_testbed != "":
        logging.info("Oasis is running on baremetal testbed [%s].",
                     baremetal_testbed)
    # Both mode needs the nested containernet since the source code dependencies
    nested_env = build_nested_env(
        nested_containernet, yaml_base_path, oasis_workspace)
    if nested_env is None:
        logging.info("Error: failed to build the nested containernet.")
        sys.exit(1)
    nested_env.start()
    nested_env.execute(
        f"python3 {g_root_path}src/run_test.py {yaml_base_path} {oasis_workspace} "
        f"{ns.tests_config_file} {debug_log}")
    nested_env.stop()
