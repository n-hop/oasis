import os
import sys
import logging
import platform
import yaml

from mininet.log import setLogLevel

from interfaces.network_mgr import NetworkType
from tools.util import (is_same_path, is_base_path, parse_test_file_name)
from var.global_var import g_root_path
from core.config import (IConfig, NodeConfig, load_all_tests)
from core.network_factory import (create_network_mgr)
from core.runner import TestRunner


def containernet_node_config(config_base_path, file_path) -> NodeConfig:
    """Load node related configuration from the yaml file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as stream:
            yaml_content = yaml.safe_load(stream)
    except FileNotFoundError:
        logging.error(
            "YAML file '%s' not found.", file_path)
        return NodeConfig(name="", img="")
    except yaml.YAMLError as exc:
        logging.error("Error parsing YAML file: %s", exc)
        return NodeConfig(name="", img="")

    if not yaml_content or 'containernet' not in yaml_content:
        logging.error("No containernet node config found in the YAML file.")
        return NodeConfig(name="", img="")
    node_config_yaml = yaml_content['containernet']["node_config"]
    loaded_conf = IConfig.load_yaml_config(config_base_path,
                                           node_config_yaml, 'node_config')
    if isinstance(loaded_conf, NodeConfig):
        # Ensure the loaded configuration is a NodeConfig
        return loaded_conf
    logging.error("Error: loaded configuration is not a NodeConfig.")
    return NodeConfig(name="", img="")


def load_containernet_config(mapped_config_path, yaml_test_file, source_workspace, original_config_path):
    # print all input parameters
    node_config = containernet_node_config(mapped_config_path, yaml_test_file)
    if node_config is None or node_config.name == "":
        logging.error("Error: no containernet node config.")
        sys.exit(1)
    # mount the workspace
    node_config.vols.append(f'{source_workspace}:{g_root_path}')
    if mapped_config_path == f'{g_root_path}config/':
        node_config.vols.append(
            f'{original_config_path}:{mapped_config_path}')
    return node_config


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
    yaml_config_base_path = sys.argv[1]
    oasis_workspace = sys.argv[2]
    logging.info("Platform: %s", platform.platform())
    logging.info("Python version: %s", platform.python_version())
    logging.info("Yaml config path: %s", yaml_config_base_path)
    logging.info("Oasis workspace: %s", oasis_workspace)
    # config_path can be
    # Not in Oasis workspace:  `{g_root_path}config/`
    # in Oasis workspace:      `{g_root_path}src/config/`
    if is_same_path(yaml_config_base_path, f"{oasis_workspace}/src/config/"):
        # oasis workspace mapped to `{g_root_path}`
        # no additional mapping is needed since oasis config is already in the path.
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
    cur_selected_test = "all"
    cur_test_file, cur_selected_test = parse_test_file_name(cur_test_file)
    if not cur_test_file:
        logging.info("Error: invalid test file name.")
        sys.exit(1)
    if not cur_selected_test:
        cur_selected_test = "all"
    yaml_test_file_path = f'{config_path}/{cur_test_file}'
    if not os.path.exists(yaml_test_file_path):
        logging.info(f"Error: %s does not exist.", yaml_test_file_path)
        sys.exit(1)

    is_using_testbed = False
    cur_hosts_config = None
    network_manager = None
    if not is_using_testbed:
        logging.info("##### running tests on containernet.")
        network_manager = create_network_mgr(NetworkType.containernet)
        cur_hosts_config = load_containernet_config(
            config_path, yaml_test_file_path, oasis_workspace, yaml_config_base_path)
    else:
        logging.info("##### running tests on testbed.")
        network_manager = create_network_mgr(NetworkType.testbed)
        cur_hosts_config = load_testbed_config(
            'testbed_nhop_shenzhen', config_path)

    if network_manager is None:
        logging.error("Error: failed to load proper network manager")
        sys.exit(1)
    # 1. execute all the tests on all constructed networks
    loaded_tests = load_all_tests(yaml_test_file_path, cur_selected_test)
    if loaded_tests is None or len(loaded_tests) == 0:
        logging.error("Error: no test case found.")
        sys.exit(1)
    for test in loaded_tests:
        cur_topology = test.load_topology(config_path)
        if not cur_topology:
            continue
        # 1.1 The topology in one case can be composed of multiple topologies:
        #      Traverse all the topologies in the test case.
        for index, cur_top_ins in enumerate(cur_topology):
            test_runner = TestRunner(test.yaml(), config_path, network_manager)
            test_runner.init(cur_hosts_config, cur_top_ins)
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
        # # for index, cur_top_ins in enumerate(cur_topology):
    # # for test in loaded_tests:
    # create a regular file to indicate the test success
    with open(f"{g_root_path}test.success", 'w', encoding='utf-8') as f_success:
        f_success.write(f"test.success")
    sys.exit(0)
