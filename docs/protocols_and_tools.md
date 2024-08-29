## 1. Protocols

Currently, Oasis supports the following protocols:

| Protocol                                              | Description                                     |
| ----------------------------------------------------- | ----------------------------------------------- |
| BTP                                                   | BATS™ Protocol                                  |
| BRTP                                                  | BATS™ Reliable Transport Protocol               |
| BRTP_PROXY                                            | BATS™ Reliable Transport Protocol in Proxy mode |
| KCP                                                   | KCP Protocol       (uses KCP-TUN)               |
| [QUIC](https://datatracker.ietf.org/doc/html/rfc9000) | A UDP-Based Multiplexed and Secure Transport    |

### 1.1 BATS Protocol

The items `BTP`, `BRTP`,`BRTP_PROXY` are BATS™ protocol. You can find the details in [BATS™](../bats/README.md).

### 1.2 KCP

[KCP](https://github.com/skywind3000/kcp) is a fast and reliable protocol that can achieve the transmission effect of a reduction of the average latency by 30% to 40% and reduction of the maximum delay by a factor of three, at the cost of 10% to 20% more bandwidth wasted than TCP.

[KCP-TUN](https://github.com/xtaci/kcptun) is a concrete application based on KCP. It uses Reed-Solomon Codes to recover lost packets.

### 1.3 QUIC

Oasis integrates the QUIC protocol by using [gost](https://gost.run/en/tutorials/protocols/quic/), it is implemented by [quic-go](https://github.com/quic-go/quic-go).

## 2. Tools

### 2.1 TCP messaging endpoint

The binary located in `bin/tcp_message/tcp_endpoint` is the tool for measuring the RTT of TCP messages over other protocols. Its source code is in [bats-documentation](https://github.com/n-hop/bats-documentation).

### 2.2 Traffic control (tc)

[`docs/tc-strategy.md`](tc-strategy.md) provides a detailed explanation of the traffic control strategy in Oasis.


build/_deps/oasis-src/src/start.py