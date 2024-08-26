## Get Started

### 1. Run test

```bash
sudo python3 src/start.py -p {base_path_of_yaml_config_files} -n nested-containernet-config.yaml --containernet=default -t protocol-single-hop-test.yaml
```

`{base_path_of_yaml_config_files}` is the path to all the yaml configuration files. Oasis will search `nested-containernet-config.yaml`, `protocol-single-hop-test.yaml` in this folder.

`--containernet=default` is the containernet configuration. `default` means use the default containernet configuration from `nested-containernet-config.yaml`.

`-t protocol-single-hop-test.yaml` is the test case file. The test case file is a YAML file that defines the test case. The test case file is located in `{base_path_of_yaml_config_files}`.

A concrete example can be as follows:

```bash
sudo python3 src/start.py -p /home/runner/oasis/src/config -n nested-containernet-config.yaml --containernet=default -t protocol-single-hop-test.yaml
```

This will run the `src/run_test.py` in a nested containernet environment. If `containernet` is installed, run the `src/run_test.py` directly:

```bash
python3 src/run_test.py {base_path_of_yaml_config_files} one-concrete-network.yaml
```

### 2. Test results

The test results are located in `{workspace}/test_results/{test_case_name}`, the test name is defined in the test case YAML file.
In this folder, there are svg files(`iperf3_throughput.svg`,`rtt.svg`, `rtt_cdf.svg`) which shows throughput and RTT performance.

## Build docker image

When use `--containernet=default`, build the docker image with the following command:

```bash
cd src/config/containernet-docker-official && docker build -t containernet:latest .
cd src/config/protocol-docker-azure && docker build -t ubuntu:22.04 .
```
