## Get Started

This guide provides simple steps to getting started with Oasis.

- [Get Started](#get-started)
  - [1. Run test](#1-run-test)
    - [1.1 Change the network topology and its parameters](#11-change-the-network-topology-and-its-parameters)
    - [1.2 Change the configuration of the test tools](#12-change-the-configuration-of-the-test-tools)
    - [1.3 Change the evaluation targets(protocol)](#13-change-the-evaluation-targetsprotocol)
  - [2. Test results](#2-test-results)
- [Build docker image](#build-docker-image)

### 1. Run test

The following command will run `src/run_test.py` in a nested containernet environment, and `run_test.py` will execute the test case defined in `protocol-performance-comparison.yaml`.

```bash
sudo python3 src/start.py -p /home/runner/oasis/src/config \
    --containernet=default \
    -t protocol-performance-comparison.yaml
```

`/home/runner/oasis/src/config` is the directory containing all the YAML configuration files. Oasis will search for `nested-containernet-config.yaml`, `protocol-single-hop-test.yaml` in this folder. This folder can be customized according to the location of Oasis repository.

`--containernet=default` specifies the Containernet configuration. `default` means use the default containernet configuration(such as docker images been used, mount points, etc) from `nested-containernet-config.yaml`.

`-t protocol-performance-comparison.yaml` specifies the test case file, which is a YAML file defining the test case. By default, it tries to execute all the test cases in that file. To execute a specific test case, use `-t protocol-performance-comparison.yaml:test_name`.

#### 1.1 Change the network topology and its parameters

In `protocol-performance-comparison.yaml`, the network topology of the case `test100` is defined in the `topology` section:

```yaml
   test100:
    topology:
      config_name: linear_network_1
      config_file: config/predefined.topology.yaml
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

#### 1.2 Change the configuration of the test tools

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

#### 1.3 Change the evaluation targets(protocol)

For each test case, we can define the target protocols to be evaluated. The following is an example:

```yaml
  test3:
    description: "Compare the performance of kcp, tcp-bbr, and QUIC in a linear network"
    target_protocols: [ kcp, tcp-bbr, quic]
```

Oasis will uses selected test tools to measure the performance of the target protocols one by one.

### 2. Test results

The test results will be saved to `{oasis_workspace}/test_results/{test_case_name}`, where `{test_case_name}` is defined in the test case YAML file. This folder contains following SVG files to show throughput and RTT performance:

- `iperf3_throughput.svg`
- `rtt.svg`,
- `rtt_cdf.svg`

`{oasis_workspace}` is the base directory of Oasis.

## Build docker image

 When using `--containernet=default`, build the Docker image with the following commands:

```bash
cd src/config/containernet-docker-official && docker build -t containernet:latest .
cd src/config/protocol-docker-azure && docker build -t ubuntu:22.04 .
```
