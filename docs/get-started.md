## Get Started

### 1. Run test

```bash
sudo python3 src/start.py -n src/config/nested-containernet-config.yaml \
    --containernet=default \
    -w {workspace} \
    -t src/config/protocol-single-hop-test.yaml
```

This will run the `src/run_test.py` in a nested containernet environment. If `containernet` is installed, run the `src/run_test.py` directly:

```bash
python3 src/run_test.py {workspace} src/config/one-concrete-network.yaml
```

`{workspace}` is the path to the root directory of the project oasis.

### 2. Test results

The test results are located in `{workspace}/test_results/{test_case_name}`, the test name is defined in the test case YAML file.
In this folder, there are svg files(`iperf3_throughput.svg`,`rtt.svg`, `rtt_cdf.svg`) which shows throughput and RTT performance.

## Build docker image

When use `--containernet=default`, build the docker image with the following command:

```bash
cd src/config/containernet-docker-official && docker build -t containernet:latest .
cd src/config/protocol-docker-azure && docker build -t ubuntu:22.04 .
```