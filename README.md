
[![Oasis CI](https://github.com/n-hop/oasis/actions/workflows/.github.ci.yml/badge.svg)](https://github.com/n-hop/oasis/actions/workflows/.github.ci.yml)
[![CodeQL](https://github.com/n-hop/oasis/actions/workflows/codeql.yml/badge.svg)](https://github.com/n-hop/oasis/actions/workflows/codeql.yml)
[![Pylint](https://github.com/n-hop/oasis/actions/workflows/pylint.yml/badge.svg)](https://github.com/n-hop/oasis/actions/workflows/pylint.yml)

-----

# Oasis

Oasis is a network emulation platform that enables protocol developers to test their protocols in diverse network topologies and conditions.

Oasis is built on [Containernet](https://github.com/containernet/containernet/), a fork of [Mininet](http://mininet.org/), and [Docker](https://www.docker.com/). It offers a web-based user interface for creating and managing testbeds, test cases, and test results. Additionally, it provides a RESTful API for interacting with the DevOps platform. One of the most impressive features of Oasis is its extensive set of components for visualizing and analyzing test results, as well as automatically generating test reports based on provided templates.

## Features

- **Web-based User Interface**: Users can create, modify, delete, and execute test cases, as well as manage versions of user-defined protocols.
- **RESTful API**: Users can interact with the DevOps platform through the API.
- **Data Visualization**: Oasis offers numerous components for visualizing test data.
- **Flexible Architecture**: Oasis can be used for pure software emulation or as a front-end for a series of real testbeds.
- **Built-in Protocol Support**: Oasis includes extensive built-in protocol support, such as TCP, KCP, QUIC, and more.
- **Built-in Dynamic Routing Support**: For complex mesh networks, Oasis offers built-in dynamic routing support.

## Get started

A simple guide to getting started with Oasis can be found in [Get Started](docs/get-started.md).

## Protocols and Tools

Detailed information can be found in [Protocols and Tools](docs/protocols_and_tools.md).

## Limitations

- **Link latency**: The valid range is 0-30ms; 0ms means no additional latency is added. And the maximum latency of each link is 30ms.
  The link latency is simulated by the Linux `tc` module, which requires sufficient queuing buffer capacity. If the queuing buffer is not large enough, `tc` module will drop packets under heavy traffic, affecting the accuracy of simulating the link loss rate.
  
- **Link bandwidth**: The valid range is 1-100Mbps. The maximum bandwidth for each link is limited because the processing rate of the BATS™ protocol binary in this repository is capped at 100Mbps. For rates higher than 100Mbps, a software license from n-hop is required.
