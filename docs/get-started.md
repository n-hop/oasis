## Get Started

### 1. Run test

```bash
sudo python3 src/start.py -p {base_path_of_yaml_config_files} \
    -n nested-containernet-config.yaml \
    --containernet=default \
    -t protocol-single-hop-test.yaml
```

`{base_path_of_yaml_config_files}` is the directory containing all the YAML configuration files. Oasis will search for `nested-containernet-config.yaml`, `protocol-single-hop-test.yaml` in this folder.

`--containernet=default` specifies the Containernet configuration. `default` means use the default containernet configuration from `nested-containernet-config.yaml`.

`-t protocol-single-hop-test.yaml` specifies the test case file, which is a YAML file defining the test case.

A concrete example is as follows:

```bash
sudo python3 src/start.py -p /home/runner/oasis/src/config \
    -n nested-containernet-config.yaml \
    --containernet=default \
    -t protocol-single-hop-test.yaml
```

This command will run `src/run_test.py` in a nested containernet environment. If Containernet is installed, you can run the `src/run_test.py` directly:

```bash
python3 src/run_test.py {base_path_of_yaml_config_files} one-concrete-network.yaml
```

### 2. Test results

The test results are located in `{oasis_workspace}/test_results/{test_case_name}`, where `{test_case_name}` is defined in the test case YAML file. This folder contains SVG files(`iperf3_throughput.svg`,`rtt.svg`, `rtt_cdf.svg`) that show throughput and RTT performance.

`{oasis_workspace}` is the base directory of Oasis.

## Build docker image

 When using `--containernet=default`, build the Docker image with the following commands:

```bash
cd src/config/containernet-docker-official && docker build -t containernet:latest .
cd src/config/protocol-docker-azure && docker build -t ubuntu:22.04 .
```
