## Get Started

### 1. Run test

```bash
sudo python3 src/start.py -n src/config/nested-containernet-config.yaml \
    --containernet=nuc_sz \
    -w {workspace} \
    -t src/config/protocol-single-hop-test.yaml
```

If image `bats_containernet:dev` is available in local, use `--containernet=nuc_sz`; otherwise, use `--containernet=default`.

This will run the `src/run_test.py` in a nested containernet environment. If you have installed the containernet, run the `src/run_test.py` directly:

```bash
python3 src/run_test.py {workspace} src/config/one-concrete-network.yaml
```

{workspace} is the path to the root directory of the project oasis.

### 2. Check test

Output of the test is located in {workspace}/test_results/{test_case_name}, the test name is defined in the test case YAML file.
In the folder, there are two diagram files which were named "iperf3_throughput.svg" and "rtt.svg". Those files shows test data of throughput and RTT.

## Build docker image

When use `--containernet=default`, build the docker image with the following command:

```bash
cd src/config/containernet-docker-official && docker build -t containernet:latest .
cd src/config/protocol-docker-azure && docker build -t ubuntu:22.04 .
```
