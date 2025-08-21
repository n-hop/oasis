# Get Started

This guide provides simple steps to getting started with Oasis.

- [Get Started](#get-started)
  - [1. Prerequisites](#1-prerequisites)
    - [Build docker image](#build-docker-image)
    - [WSL kernel recompile](#wsl-kernel-recompile)
  - [2. Run test](#2-run-test)
    - [2.1 Change the network topology and its parameters](#21-change-the-network-topology-and-its-parameters)
    - [2.2 Change the configuration of the test tools](#22-change-the-configuration-of-the-test-tools)
    - [2.3 Change the evaluation targets(protocol)](#23-change-the-evaluation-targetsprotocol)
    - [2.4 Built-in routing strategies](#24-built-in-routing-strategies)
  - [3. Test results](#3-test-results)
  - [4. Customize protocol definition](#4-customize-protocol-definition)
    - [4.1 protocol yaml description](#41-protocol-yaml-description)
    - [4.2 iteration description](#42-iteration-description)
    - [4.3 Root files](#43-root-files)

## 1. Prerequisites

First step is to get the source code of Oasis from GitHub:

```bash

git clone https://github.com/n-hop/oasis.git

```

For Linux platform, uses the instructions in [Build docker image](#build-docker-image) to build the docker image before running the test.

For Windows platform, WSL with traffic control (tc) support is required. Please follow the instructions in [WSL kernel recompile](#wsl-kernel-recompile) to recompile the WSL kernel with tc support.

> Note: Highly recommend to use Oasis with Ubuntu 22.04.

### Build docker image

 When using `--containernet=official`, build the Docker image with the following commands:

```bash
cd src/config/containernet-docker-official && docker build -t containernet:latest .
cd src/config/protocol-docker-azure && docker build -t ubuntu:22.04 .
```

### WSL kernel recompile

When using WSL in windows, tc is not default compiled to WSL kernel, so WSL kernel recompilation with tc support is needed, script is provided in {project_dir}/bin/wsl_kernel_support/kernel_tc.sh

First open Windows PowerShell

```bash

wsl --unregister Ubuntu-22.04   # unregister any installed wsl
wsl --install Ubuntu-22.04      # reinstall wsl Ubuntu-22.04
```

After setup username and password, copy kernel_tc.sh to home directory (~)

```bash
sudo CUR_USER=$USER ./kernel_tc.sh
```

After kernel recompiled, open Windows Powershell

```bash
wsl --shutdown      # reset wsl
```

Open new wsl terminal and check if wsl support tc

```bash
sudo tc q                                       # check existing tc rules
sudo tc qdisc add dev eth0 root netem loss 10%  # add 10% packet drop rate to eth0 interface
```

## 2. Run test

The following command will run `src/run_test.py` in a nested containernet environment, and `run_test.py` will execute the test case defined in `protocol-performance-comparison.yaml`.

```bash
# in the root directory of oasis project
sudo python3 src/start.py -p src/config \
    --containernet=official \
    -t protocol-performance-comparison.yaml
```

`src/config` is the directory containing all the YAML configuration files. Oasis will search for `nested-containernet-config.yaml`, `protocol-single-hop-test.yaml` in this folder. This folder can be customized according to the location of Oasis repository.

`--containernet=official` specifies the official Containernet configuration which is defined in `nested-containernet-config.yaml`.

`-t protocol-performance-comparison.yaml` specifies the test case file, which is a YAML file defining the test case. By default, it tries to execute all the test cases in that file. To execute a specific test case, use `-t protocol-performance-comparison.yaml:test_name`.

### 2.1 Change the network topology and its parameters

In `protocol-performance-comparison.yaml`, the network topology of the case `test100` is defined in the `topology` section:

```yaml
   test100:
    topology:
      config_name: linear_network_1
      config_file: predefined.topology.yaml
```

The case `test100` will use the `linear_network_1` topology defined in `config/predefined.topology.yaml`. And `linear_network_1` is defined as follows:

```yaml
- name: linear_network_1
    topology_type: linear
    nodes: 2
    array_description:
      - link_loss:
        init_value: [5]
      - link_latency:
        init_value: [10]
      - link_jitter:
        init_value: [0]
      - link_bandwidth_forward:
        init_value: [100]
      - link_bandwidth_backward:
        init_value: [100]
```

To change the network topology, we can change the value of `nodes`. If values of `nodes` is `N`, it is a `N-1` hops of chain network. Other editable parameters are `link_loss`, `link_latency`, `link_jitter`, `link_bandwidth_forward`, and `link_bandwidth_backward`. Those arrays are used to define the link attributes of the network link by link from the node 0 to node N-1.

"array_description" is only suitable for linear topology. For other topologies, the parameters should be defined by "json_description". The following is an example of a 4-hops linear network:

```yaml
  - name: 4-hops-linear-network
    topology_type: linear
    nodes: 5
    json_description: config/4-hops-linear-network.json
```

"json_description" uses adjacent matrices to describe the network topology and its link attributions which is quite easy to understand.

Also, we provide the way to define topology in the test case file directly. The following is an example:

```yaml
   test100:
    topology:
        topology_type: linear
        nodes: 2
        array_description:
        - link_loss:
            init_value: [5]
        - link_latency:
            init_value: [10]
        - link_jitter:
            init_value: [0]
        - link_bandwidth_forward:
            init_value: [100]
        - link_bandwidth_backward:
            init_value: [100]
```

### 2.2 Change the configuration of the test tools

Details of supported test tools can be found in [Protocols and Tools](protocols_and_tools.md#2-tools).

`tcp_message_endpoint` is used to measure the RTT of TCP messages over other protocols. It can be added to the test case file as follows:

```yaml
   test100:
    test_tools:
      rtt:
        interval: 0.01
        packet_count: 1
        packet_size: 20
        client_host: 0
        server_host: 3
```

With the above configuration, the `tcp_message_endpoint` tool will be used to measure the RTT of TCP messages between host 0 and host 3.

Other parameters are:

 - `interval` represents the interval between two packets; it is also the message sending rate of the tool; `0.01` means 100 messages per second;
 - `packet_count` is the number of messages to be sent;
 - `packet_size` is the size of each message in bytes;

If only care about the RTT of the first message, set `packet_count` to 1.

### 2.3 Change the evaluation targets(protocol)

For each test case, we can define the target protocols to be evaluated. The following is an example:

```yaml
  test3:
    description: "Compare the performance of kcp, tcp-bbr with a linear network"
    target_protocols: [kcp, tcp-bbr]
```

Oasis will uses selected test tools to measure the performance of the target protocols one by one.

### 2.4 Built-in routing strategies

In the test case, the applied routing strategy of current test is specified by `route`:

```yaml
  - name: test001
    route: static_route
```

Currently supported route strategies are:

- `static_route`, static routing which are configured with `ip route add` command. This works for the chain network.
- `static_bfs`, static routing which are configured with `ip route add` command. This works for the mesh network, including the chain one.
- `olsr`, dynamic routing configuration which are done by `OSLR` protocol daemon. This works for the chain network.

## 3. Test results

The test results will be saved to `{oasis_workspace}/test_results/{test_case_name}`, where `{test_case_name}` is defined in the test case YAML file. This folder contains following SVG files to show throughput and RTT performance:

- `iperf3_throughput.svg`
- `rtt.svg`,
- `rtt_cdf.svg`

`{oasis_workspace}` is the base directory of Oasis.

## 4. Customize protocol definition

### 4.1 protocol yaml description

For a distributed protocol, it can be defined in the `predefined.protocols.yaml` file as follows:

```yaml
  - name: btp
    type: distributed
    bin: bats_protocol
    args:
      - "--daemon_enabled=true"
      - "--tun_protocol=BTP"
    version: latest
```

- type: 
  - `distributed` means the protocol instance should be run in every host of the network;
  - `none_distributed` means the protocol instance should be run in only specified hosts, such as client and server;
- bin: the name of the protocol binary, which should be in the `src/config/rootfs/usr/bin/` folder; or in the folder `{config_folder}/rootfs/usr/bin/` specified by `-p {config_folder}` in the `src/run_test.py` command;
- args: run-time arguments of the protocol binary;
- version: the version of the protocol binary;

### 4.2 iteration description

Iteration description is used to define the usage of one protocol binary which will play different roles(client/server) in different hosts. The following is an example:

```yaml
  - name: btp
    type: none_distributed
    args:
      - "--daemon_enabled=true"
    protocols: # iterative
      - name: btp_client
        bin: bats_protocol
        args:
          - "--tun_protocol=BTP"
        config_file: cfg-template/bats-quic-client.ini
        version: latest
      - name: btp_server
        bin: bats_protocol
        args:
          - "--tun_protocol=BRTP"
        config_file: cfg-template/bats-quic-server.ini
        version: latest
```

The protocol `btp` has two iterations: `btp_client` and `btp_server`. Those two iterations share the same `type` and `args` parameters in top-level.

### 4.3 Root files

Either `src/config/rootfs/usr/bin/` or `{config_folder}/rootfs/usr/bin/`(specified by `-p {config_folder}` in the `src/run_test.py` command) folder contains the necessary files which will be mounted into containernet(if it is in containernet mode).

In order to run the protocol binary or test tools successfully, necessary files should be copied to the `src/config/rootfs/usr/bin/` or `{config_folder}/rootfs/usr/bin/` folder.
