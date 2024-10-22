import os
import sys
import logging
import platform
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from interfaces.network_mgr import NetworkType
from containernet.topology import ITopology
from containernet.linear_topology import LinearTopology
from containernet.config import (IConfig, NodeConfig)
from tools.util import (is_same_path, is_base_path)
from var.global_var import g_root_path
from core.network_factory import (create_network_mgr)
from core.runner import TestRunner


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


def prepare_node_config(mapped_config_path, yaml_test_file, source_workspace, original_config_path):
    # print all input parameters
    node_config = load_node_config(
        mapped_config_path, yaml_test_file)
    if node_config is None or node_config.name == "":
        logging.error("Error: no containernet node config.")
        sys.exit(1)
    # mount the workspace
    node_config.vols.append(f'{source_workspace}:{g_root_path}')
    if mapped_config_path == f'{g_root_path}config/':
        node_config.vols.append(
            f'{original_config_path}:{mapped_config_path}')
    return node_config


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
    if loaded_conf.topology_type == "linear":  # type: ignore
        built_net_top = LinearTopology(loaded_conf)  # type: ignore
    else:
        logging.error("Error: unsupported topology type.")
        return None  # type: ignore
    return built_net_top


def load_testbed_config(name, yaml_base_path_input):
    absolute_path_of_testbed_config_file = os.path.join(
        yaml_base_path_input + "/", 'testbed/predefined.testbed.yaml')
    if not os.path.exists(f'{absolute_path_of_testbed_config_file}'):
        logging.info(f"Error: %s does not exist.", {
                     absolute_path_of_testbed_config_file})
        return None
    all_testbeds = None
    with open(absolute_path_of_testbed_config_file, 'r', encoding='utf-8') as stream:
        try:
            all_testbeds = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    logging.debug("all_testbeds: %s", all_testbeds)
    for testbed in all_testbeds.keys():
        if name == testbed:
            logging.info("found the testbed: %s", all_testbeds[testbed])
            return all_testbeds[testbed]
    logging.error("Testbed %s is not found.", name)
    logging.info("The supported testbeds are: %s",
                 all_testbeds.keys())
    return None


if __name__ == '__main__':
    debug_log = 'False'
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
    # config_path can be `{g_root_path}config/` or `{g_root_path}src/config/`
    if is_same_path(yaml_config_base_path, f"{oasis_workspace}/src/config/"):
        # oasis workspace mapped to `{g_root_path}`
        logging.info("No config path mapping is needed.")
        config_path = f'{g_root_path}src/config/'
    else:
        # oasis yaml config files mapped to `{g_root_path}config/`
        config_path = f'{g_root_path}config/'
        logging.info(
            "Oasis yaml config files mapped to `%s`.", config_path)
    oasis_mapped_prefix = f'{g_root_path}'
    logging.info(
        f"run_test.py: Base path of the oasis project: %s", oasis_workspace)
    running_in_nested = not is_base_path(os.getcwd(), oasis_workspace)
    if not running_in_nested:
        logging.info("Nested containernet environment is required.")
        sys.exit(1)

    cur_test_file = sys.argv[3]
    cur_selected_test = ""
    temp_list = cur_test_file.split(":")
    if len(temp_list) not in [1, 2]:
        logging.info("Error: invalid test case file format.")
        sys.exit(1)
    if len(temp_list) == 2:
        cur_test_file = temp_list[0]
        cur_selected_test = temp_list[1]
    yaml_test_file_path = f'{config_path}/{cur_test_file}'
    if not os.path.exists(yaml_test_file_path):
        logging.info(f"Error: %s does not exist.", yaml_test_file_path)
        sys.exit(1)

    is_using_testbed = False
    cur_node_config = None
    network_manager = None
    if not is_using_testbed:
        logging.info("##### running tests on containernet.")
        network_manager = create_network_mgr(NetworkType.containernet)
        cur_node_config = prepare_node_config(
            config_path, yaml_test_file_path, oasis_workspace, yaml_config_base_path)
    else:
        logging.info("##### running tests on testbed.")
        network_manager = create_network_mgr(NetworkType.testbed)
        cur_node_config = load_testbed_config(
            'testbed_nhop_shenzhen', config_path)

    if network_manager is None:
        logging.error("Error: failed to load proper network manager")
        sys.exit(1)
    # 1. execute all the tests on all constructed networks
    all_tests = load_test(yaml_test_file_path, cur_selected_test)
    if all_tests is None:
        logging.error("Error: no test case found.")
        sys.exit(1)
    for test in all_tests:
        cur_topology = load_topology(config_path, test)
        # 1.1 The topology in one case can be composed of multiple topologies:
        #      Traverse all the topologies in the test case.
        for index, cur_top_ins in enumerate(cur_topology):
            test_runner = TestRunner(
                test, config_path, network_manager)
            test_runner.init(cur_node_config,
                             cur_top_ins)
            if not test_runner.is_ready():
                test_runner.handle_failure()
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
    # create a regular file to indicate the test success
    with open(f"{g_root_path}test.success", 'w', encoding='utf-8') as f_success:
        f_success.write(f"test.success")
    sys.exit(0)
