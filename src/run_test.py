import os
import sys
import logging
import yaml

from mininet.log import setLogLevel
from containernet.linear_net import LinearNet
from containernet.containernet import PairNet
from containernet.node_config import NodeConfig


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

    cur_workspace = sys.argv[1]
    cur_config_yaml_file_path = sys.argv[2]

    if not os.path.exists(cur_config_yaml_file_path):
        logging.info(f"Error: %s does not exist.", cur_config_yaml_file_path)
        sys.exit(1)
    pair_net = build_network(cur_config_yaml_file_path)
