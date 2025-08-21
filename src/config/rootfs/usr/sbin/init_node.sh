#!/bin/sh
# This script is executed by the init process of each node in the network.
init_ssh() {
    echo "Initializing SSH for the node..."
    rm -rf /root/.ssh/
    mkdir -p /root/.ssh
    cp /root/oasis/src/config/keys/* /root/.ssh/
    cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys
    # fix: Permissions 0644 for '/root/.ssh/id_rsa' are too open
    chmod 600 /root/.ssh/id_rsa
    chmod 600 /root/.ssh/id_rsa.pub
    echo 'PermitRootLogin yes' | tee -a /etc/ssh/sshd_config
    echo 'PasswordAuthentication no' | tee -a /etc/ssh/sshd_config
    echo 'StrictModes no' | tee -a /etc/ssh/sshd_config
    service ssh start
}

init_library() {
    echo "Initializing libraries for the node..."
}

init_ssh
init_library
