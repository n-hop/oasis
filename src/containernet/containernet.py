import logging
import os
import random
import yaml
from .config import (NestedConfig)


def load_nested_config(nested_config_file: str,
                       containernet_name: str) -> NestedConfig:
    """
    Load the nested configuration from a yaml file.
    """
    if nested_config_file == "" or containernet_name == "":
        return None
    containernet_list = []
    logging.info(
        f"process yaml file: %s", {nested_config_file})
    with open(nested_config_file, 'r', encoding='utf-8') as stream:
        try:
            nested_config = yaml.safe_load(stream)
            logging.info(
                f"loaded nested_config: %s", nested_config)
            containernet_list = nested_config["containernet"]
        except yaml.YAMLError as exc:
            logging.error(exc)
            return None
    containernet_names = containernet_list.keys()
    logging.info(
        f"loaded containernet: %s", containernet_list)
    for containernet in containernet_names:
        if containernet == containernet_name:
            logging.info(
                f"loaded containernet: %s", containernet_list[containernet])
            return NestedConfig(**containernet_list[containernet])
    return None


class NestedContainernet():
    """NestedContainernet is used to initialize the Nested Containernet
    environment; then, users can use `execute` to run the test cases
    on the Nested Containernet.
    """

    def __init__(self, config: NestedConfig, yaml_base_path: str, oasis_workspace: str, test_name: str):
        self.config = config
        self.yaml_base_path = yaml_base_path
        self.oasis_workspace = oasis_workspace
        self.test_name = test_name
        self.test_container_name = ""
        self.setUp()

    def setUp(self) -> None:
        logging.info(
            "########################## Oasis setup "
            "Nested Containernet##########################")
        self.formatted_mounts = self.get_formatted_mnt()

    def tearDown(self) -> None:
        logging.info(
            "NestedContainernet tearDown the Containernet.")
        mount_config = os.path.join(self.oasis_workspace, "config")
        if os.path.exists(mount_config):
            os.system(f"umount {mount_config}")
            os.system(f"rm -rf {mount_config}")
        # unmount the mounted directories
        unmount_cmd = f"docker exec {self.test_container_name} "\
                      f"/bin/bash -c \"umount /root/config/ || true \""
        os.system(unmount_cmd)
        # stop all the running containers with the name "containernet**"
        os.system(
            "docker stop $(docker ps -a -q "
            f"-fname={self.test_container_name}) || true")
        os.system("docker container prune --force || true")
        logging.info(
            "########################## Oasis teardown"
            "NestedContainernet##########################")

    def stop(self):
        self.tearDown()

    def start(self):
        # NestedContainernet, use case file name as the container name.
        self.test_container_name = "nested_containernet_" + \
            str(random.randint(0, 1000)) + "_" + self.test_name
        logging.info(
            "Nested Containernet start... %s", self.test_container_name)
        start_cmd = "docker run -d -t --rm"
        # strip spaces in the name
        self.test_container_name = self.test_container_name.replace(" ", "")
        start_cmd += f" --name '{self.test_container_name}'"
        start_cmd += f" --hostname '{self.test_container_name}'"
        if self.config.dns_server is not None:
            for dns_server in self.config.dns_server:
                start_cmd += f" --dns='{dns_server}'"
        if self.config.dns_resolve is not None:
            for dns_resolve in self.config.dns_resolve:
                start_cmd += f" --add-host='{dns_resolve}'"
        if self.config.privileged:
            start_cmd += " --privileged "
        start_cmd += f" --network {self.config.network_mode}"
        start_cmd += f" --pid {self.config.network_mode}"
        start_cmd += f" {self.formatted_mounts}"
        start_cmd += f" {self.config.image}"
        logging.debug(
            f"Nested Containernet start_cmd: %s", start_cmd)
        ret = os.system(start_cmd)
        if ret == 0:
            self.install_dependencies()
        return ret == 0

    def install_dependencies(self):
        if not os.path.exists(f"{self.oasis_workspace}/src/containernet/requirements.txt"):
            return
        install_cmd = f"docker exec {self.test_container_name} "\
            f"/bin/bash -c \"python3 -m pip install -r /root/src/containernet/requirements.txt"\
            f" -i https://pypi.tuna.tsinghua.edu.cn/simple\""
        logging.info(
            f"Oasis execute install command \" %s \"", install_cmd)
        os.system(install_cmd)

    def patch(self):
        '''Apply patches to the nested containernet source code.'''
        for _, _, files in os.walk(f"/root/patch"):
            for patch_file in files:
                if patch_file.endswith(".patch"):
                    patch_cmd = f"docker exec {self.test_container_name} "\
                        f"/bin/bash -c \"cd / && patch -p0 < /root/patch/{patch_file}\""
                    os.system(patch_cmd)
                    logging.info(
                        f"Oasis execute patch command \" %s \"", patch_cmd)

    def execute(self, cmd):
        test_case_cmd = f"docker exec {self.test_container_name} "\
            f"/bin/bash -c \"{cmd}\""
        clean_cmd = f"docker exec {self.test_container_name} "\
            f"/bin/bash -c \"mn --clean >/dev/null 2>&1\" || true"
        logging.info(
            f"Oasis execute with \" %s \"", test_case_cmd)
        os.system(clean_cmd)
        os.system(test_case_cmd)
        os.system(clean_cmd)

    def get_formatted_mnt(self) -> str:
        logging.info(
            f"Nested Containernet config mounts: %s", self.config.mounts)
        if self.config.mounts is None:
            return ""
        # 1. mount oasis_workspace directory to /root
        self.formatted_mounts = f" --mount "\
            f"type=bind,source={self.oasis_workspace},"\
            f"target=/root,bind-propagation=shared "
        # 2. mount yaml_base_path directory to /root/config/
        self.formatted_mounts += f" --mount "\
            f"type=bind,source={self.yaml_base_path},"\
            f"target=/root/config/,bind-propagation=shared "

        for mount in self.config.mounts:
            source, target, *readonly = mount.split(":")
            if len(readonly) == 0:
                mount_cmd = f"--mount "\
                    f"type=bind,source={source},"\
                    f"target={target},bind-propagation=shared "
            else:
                mount_cmd = f"--mount "\
                    f"type=bind,source={source},"\
                    f"target={target},readonly,bind-propagation=shared "
            self.formatted_mounts += mount_cmd
        logging.info(
            f"Nested Containernet formatted mounts: %s", self.formatted_mounts)
        return self.formatted_mounts
