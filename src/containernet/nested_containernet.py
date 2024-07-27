import logging
import os
from dataclasses import dataclass, field
from typing import Optional, List
import random
import yaml


@dataclass
class NestedConfig:
    """
    NestedConfig is a dataclass that holds the configuration for the Nested Containernet.
    """
    image: str
    privileged: Optional[bool] = field(default=True)
    network_mode: Optional[str] = field(default="host")
    dns_server: Optional[List[str]] = field(default=None)
    dns_resolve: Optional[List[str]] = field(default=None)
    mounts: Optional[List[str]] = field(default=None)


def load_nested_config(nested_config_file: str, nested_containernet: str) -> NestedConfig:
    """
    Load the nested configuration from a yaml file.
    """
    if nested_config_file == "" or nested_containernet == "":
        return None
    containernet_list = []
    with open(nested_config_file, 'r') as stream:
        try:
            nested_config = yaml.safe_load(stream)
            containernet_list = nested_config["containernet"]
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    containernet_names = containernet_list.keys()
    for containernet in containernet_names:
        if containernet == nested_containernet:
            logging.info(
                f"loaded containernet: {containernet_list[containernet]}")
            return NestedConfig(**containernet_list[containernet])
    return None


class NestedContainernet():

    def __init__(self, config: NestedConfig, workspace: str, test_name: str):
        self.config = config
        self.workspace = workspace
        self.test_name = test_name
        self.setUp()

    def setUp(self) -> None:
        logging.info(
            "########################## Test Framework setup NestedContainernet ##########################")
        self.formatted_mounts = self.get_formatted_mnt()

    def tearDown(self) -> None:
        logging.info(
            f"NestedContainernet tearDown the Containernet.")
        # stop all the running containers with the name "nested_containernet**"
        os.system(
            "docker stop $(docker ps -a -q -fname=nested_containernet) || true")
        os.system("docker container prune --force || true")
        logging.info(
            "########################## Test Framework teardown NestedContainernet ##########################")

    def stop(self):
        self.tearDown()

    def start(self):
        # NestedContainernet, use case file name as the container name.
        self.test_container_name = "nested_containernet_" + \
            str(random.randint(0, 1000)) + "_" + self.test_name
        logging.info(
            f"NestedContainernet start the Containernet.")
        start_cmd = "docker run -d -t --rm "
        start_cmd += f" --name '{self.test_container_name}' "
        start_cmd += f" --hostname '{self.test_container_name}' "
        if self.config.dns_server is not None:
            for dns_server in self.config.dns_server:
                start_cmd += f" --dns='{dns_server}' "
        if self.config.dns_resolve is not None:
            for dns_resolve in self.config.dns_resolve:
                start_cmd += f" --add-host='{dns_resolve}' "
        if self.config.privileged:
            start_cmd += " --privileged "
        start_cmd += f" --network {self.config.network_mode} "
        start_cmd += f" --pid {self.config.network_mode} "
        start_cmd += f" {self.formatted_mounts} "
        start_cmd += f" {self.config.image}"
        logging.info(
            f"NestedContainernet start_cmd: {start_cmd}")
        ret = os.system(start_cmd)
        return ret == 0

    def execute(self, cmd):
        test_case_cmd = f"docker exec {self.test_container_name} /bin/bash -c \"{cmd}\""
        clean_cmd = f"docker exec {self.test_container_name} /bin/bash -c \"mn --clean >/dev/null 2>&1\" || true"
        logging.info(
            "########################## Test Framework NestedContainernet Executing... ##########################")
        logging.info(
            f"execute with \" {test_case_cmd} \"")
        os.system(clean_cmd)
        os.system(test_case_cmd)
        os.system(clean_cmd)

    def get_formatted_mnt(self) -> str:
        logging.info(
            f"NestedContainernet config mounts: {self.config.mounts}")
        if self.config.mounts is None:
            return ""
        self.formatted_mounts = f" --mount type=bind,source={self.workspace},target=/root,bind-propagation=shared "
        for mount in self.config.mounts:
            source, target, *readonly = mount.split(":")
            if len(readonly) == 0:
                mount_cmd = f"--mount type=bind,source={source},target={target},bind-propagation=shared "
            else:
                mount_cmd = f"--mount type=bind,source={source},target={target},readonly,bind-propagation=shared "
            self.formatted_mounts += mount_cmd
        logging.info(
            f"NestedContainernet formatted mounts: {self.formatted_mounts}")
        return self.formatted_mounts
