import os
import sys
import logging
import yaml

# from mininet.cli import CLI
from mininet.log import setLogLevel
from containernet.linear_topology import LinearTopology
from containernet.network import Network
from containernet.config import NodeConfig


def build_network(yaml_file_path):
    # TODO(.): chain of responsibility
    with open(yaml_file_path, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    net = LinearTopology(yaml_content['topology'])
    config = NodeConfig(** yaml_content['node_config'])
    return Network(config, net)


if __name__ == '__main__':
    # set log level
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
