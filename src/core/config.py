"""
    A Wrapper for the mininet Host (Node)

"""
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import logging
import os
import yaml

from .topology import (ITopology, TopologyConfig)
from .linear_topology import LinearTopology
from .mesh_topology import MeshTopology


@dataclass
class NodeConfig:
    """Configuration for the Docker node.
    """
    name: str
    img: str
    vols: List[str] = field(default_factory=list)
    bind_port: Optional[bool] = field(default=True)
    name_prefix: Optional[str] = field(default='h')  # h i j k.
    ip_range: Optional[str] = field(default='10.0.0.0/8')
    # the script to run when the node starts(after routes are set)
    init_script: Optional[str] = field(default="")
    config_base_path: Optional[str] = field(default="")


@dataclass
class NestedConfig:
    """
    NestedConfig is a dataclass that holds
    the configuration for the Nested Containernet.
    """
    image: str
    privileged: Optional[bool] = field(default=True)
    containernet_repo_from_user: Optional[bool] = field(default=False)
    containernet_repo_path: Optional[str] = field(default="/containernet")
    network_mode: Optional[str] = field(default="host")
    dns_server: Optional[List[str]] = field(default=None)
    dns_resolve: Optional[List[str]] = field(default=None)
    mounts: Optional[List[str]] = field(default=None)


supported_config_keys = ["topology", "node_config"]


class IConfig(ABC):
    @staticmethod
    def is_supported_config_key(config_key: str):
        return config_key in supported_config_keys

    @staticmethod
    def load_config_reference(config_base_path: str, yaml_config_file: str,
                              config_name: str, scripts: str, config_key: str):
        if not IConfig.is_supported_config_key(config_key):
            logging.error(
                f"load_config_reference: key %s is not supported.",
                config_key)
            return None
        full_yaml_config_file = os.path.join(
            config_base_path, yaml_config_file)
        if not os.path.exists(full_yaml_config_file):
            logging.error(
                f"load_config_reference: file %s does not exist.",
                full_yaml_config_file)
            return None
        try:
            with open(full_yaml_config_file, 'r', encoding='utf-8') as stream:
                loaded_yaml_config = yaml.safe_load(stream)
        except FileNotFoundError:
            logging.error(
                "YAML file '%s' not found.", full_yaml_config_file)
            return None
        except yaml.YAMLError as exc:
            logging.error("Error parsing YAML file: %s", exc)
            return None

        # check key 'config_key' in the yaml content
        if loaded_yaml_config is None or config_key not in loaded_yaml_config:
            logging.error(
                f"load_config_reference: %s is not defined in %s",
                config_key, full_yaml_config_file)
            return None
        loaded_config = None
        # Find it by 'name' in `node_config`, for example "linear_network"
        for conf in loaded_yaml_config[config_key]:
            if conf['name'] == config_name:
                loaded_config = conf
                logging.info('load_config_reference: loaded %s', loaded_config)
                break
        if loaded_config is None:
            logging.error(
                f"load_config_reference: %s is not defined in %s",
                config_name, full_yaml_config_file)
            return None
        if config_key == "node_config":
            loaded_config["init_script"] = scripts
            return NodeConfig(**loaded_config)
        if config_key == "topology":
            return TopologyConfig(**loaded_config)
        return None

    @staticmethod
    def load_yaml_config(config_base_path: str, yaml_description: Dict[str, Any], config_key: str):
        # load it directly from the yaml_description or
        # load it from another yaml file.
        if not IConfig.is_supported_config_key(config_key):
            logging.error(
                f"load_yaml_config: key %s is not supported.",
                config_key)
            return None
        init_script = yaml_description.get('init_script', "")
        is_load_from_file = ["config_file", "config_name"]
        if all(key in yaml_description for key in is_load_from_file):
            # load from the yaml file `config_file`
            return IConfig.load_config_reference(
                config_base_path,
                yaml_description['config_file'],
                yaml_description['config_name'],
                init_script,
                config_key)
        # load directly from the yaml_description
        logging.info('load_yaml_config: %s', yaml_description)
        if config_key == "node_config":
            return NodeConfig(**yaml_description)
        if config_key == "topology":
            return TopologyConfig(**yaml_description)
        return None


class Test:
    """Class to hold the test configuration(yaml) for one cases
    """

    def __init__(self, test_yaml: Dict[str, Any], name: str):
        self.name = name
        self.test_yaml = test_yaml

    def yaml(self):
        return self.test_yaml

    def is_active(self):
        if not self.test_yaml:
            return False
        if "if" in self.test_yaml and not self.test_yaml["if"]:
            return False
        return True

    def load_topology(self, config_base_path) -> Optional[ITopology]:
        """Load network related configuration from the yaml file.
        """
        if 'topology' not in self.test_yaml:
            logging.error("Error: missing key topology in the test case yaml.")
            return None
        local_yaml = self.test_yaml['topology']
        logging.info(f"Test: local_yaml %s",
                     local_yaml)
        if local_yaml is None:
            logging.error("Error: content of topology is None.")
            return None
        loaded_conf = IConfig.load_yaml_config(config_base_path,
                                               local_yaml,
                                               'topology')
        if loaded_conf is None or not isinstance(loaded_conf, TopologyConfig):
            logging.error("Error: loaded_conf of topology is None.")
            return None
        if loaded_conf.topology_type == "linear":
            return LinearTopology(config_base_path, loaded_conf)
        if loaded_conf.topology_type == "mesh":
            return MeshTopology(config_base_path, loaded_conf, True)
        logging.error("Error: unsupported topology type.")
        return None


def load_all_tests(test_yaml_file: str, test_name: str = "all") -> List[Test]:
    """
        Load the test case configuration from a yaml file.
    """
    logging.info(
        "########################## Oasis Loading Tests "
        "##########################")
    try:
        with open(test_yaml_file, 'r', encoding='utf-8') as stream:
            yaml_content = yaml.safe_load(stream)
    except FileNotFoundError:
        logging.error("Test YAML file '%s' not found.", test_yaml_file)
        return []
    except yaml.YAMLError as exc:
        logging.error("Error parsing YAML file: %s", exc)
        return []
    if not yaml_content or 'tests' not in yaml_content:
        logging.error("No tests found in the YAML file.")
        return []
    test_cases = yaml_content["tests"]
    # ------------------------------------------------
    if test_cases is None:
        logging.error("No test cases are loaded from %s", test_yaml_file)
        return []
    active_test_list = []
    if test_name in ("all", "All", "ALL"):
        test_name = ""
    for name in test_cases.keys():
        if test_name not in ("", name):
            logging.debug("Oasis skips the test case %s", name)
            continue
        test_cases[name]["name"] = name
        test = Test(test_cases[name], name)
        if test.is_active():
            active_test_list.append(test)
            logging.info(f"case %s is enabled!", name)
        else:
            logging.info(f"case %s is disabled!", name)
    if len(active_test_list) == 0:
        logging.info(f"No active test case in %s", test_yaml_file)
    return active_test_list
