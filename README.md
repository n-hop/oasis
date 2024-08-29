
[![Oasis CI](https://github.com/n-hop/oasis/actions/workflows/.github.ci.yml/badge.svg)](https://github.com/n-hop/oasis/actions/workflows/.github.ci.yml)
[![CodeQL](https://github.com/n-hop/oasis/actions/workflows/codeql.yml/badge.svg)](https://github.com/n-hop/oasis/actions/workflows/codeql.yml)
[![Pylint](https://github.com/n-hop/oasis/actions/workflows/pylint.yml/badge.svg)](https://github.com/n-hop/oasis/actions/workflows/pylint.yml)

-----

# Oasis

Oasis is a network emulation platform that allows protocol developers to test their protocols in any network topology with various network conditions.

Oasis is built on top of [Containernet](https://github.com/containernet/containernet/), a fork of [Mininet](http://mininet.org/), and [Docker](https://www.docker.com/). It provides a web-based user interface for users to create and manage testbeds, test cases, and test results. It also provides a RESTful API for users to interact with the DevOps platform. And the most impressive feature of Oasis is that it provides a lot of components for users to visualize, analyze the test results, and even generate the test report automatically based on given templates.

## Features

- **Web-based User Interface**: Users can create/modify/delete/execute test cases, also can manage the version of user defined protocol.
- **RESTful API**: Users can interact with the DevOps platform via the API.
- **Data Visualization**: Oasis provides a lot of components for users to visualize the test data.
- **Flexible architecture**: Oasis can be used as a pure software emulation, also it can be used as a front-end for a series of real testbed.
- **Built-in protocol support**: Oasis provides a lot of built-in protocol support, such as TCP, KCP, QUIC, etc.
- **Built-in dynamic routing support**: For the complex mesh network, Oasis provides a built-in dynamic routing support.

## Get started

A simple guide to get started with Oasis can be found in [Get Started](docs/get-started.md).

## Protocols and Tools

Find details in [Protocols and Tools](docs/protocols_and_tools.md).

## Limitations

- **Link latency**: valid range is 0-30ms; 0ms means no additional latency is added. And the maximum latency of each link is 30ms.
  The link latency is simulated by the Linux `tc` module, which has requirements on the capacity of the queuing buffer. If the queuing buffer is not large enough, `tc` module will drop packets when the traffic is heavy and it affects the accuracy of simulating the link loss rate.
  
- **Link bandwidth**: valid range is 1-100Mbps; we limit the maximum bandwidth of each link for reasons that the processing rate of BATS™ protocol binary in this repository is limited to 100Mbps; and for the rate higher than 100Mbps, it requires a software license from n-hop.
