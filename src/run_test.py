import os
import sys
import logging
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from containernet.linear_topology import LinearTopology
from containernet.topology import ITopology
from containernet.network import Network
from containernet.config import NodeConfig


def build_network(yaml_file_path):
    """Build a container network from the yaml configuration file.

    Args:
        yaml_file_path (str): the path of the yaml configuration file

    Returns:
        Network: the container network object
    """
    with open(yaml_file_path, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    top_config = ITopology.load_yaml_config(yaml_content['topology'])
    if top_config is None:
        logging.error("Error: topology configuration is None.")
        return None
    net_top = None
    if top_config.topology_type == "linear":
        net_top = LinearTopology(top_config)
    else:
        logging.error("Error: unsupported topology type.")
        return None
    node_config = NodeConfig(** yaml_content['node_config'])
    return Network(node_config, net_top)


if __name__ == '__main__':
    setLogLevel('info')
    logging.basicConfig(level=logging.INFO)

    cur_workspace = sys.argv[1]
    cur_config_yaml_file_path = sys.argv[2]

    if not os.path.exists(cur_config_yaml_file_path):
        logging.info(f"Error: %s does not exist.", cur_config_yaml_file_path)
        sys.exit(1)
    linear_network = build_network(cur_config_yaml_file_path)
    linear_network.build()
    linear_network.start()

    linear_network.check_connectivity()

    linear_network.stop()
