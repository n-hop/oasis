## 1. Protocols

Oasis currently supports the following protocols:

| Protocol   | Description                                                                        |
| ---------- | ---------------------------------------------------------------------------------- |
| btp        | BATS™ Transport Protocol (the framework, multi-hop version)                        |
| brtp       | BATS™ Reliable Transport Protocol (the framework, multi-hop version)               |
| brtp_proxy | BATS™ Reliable Transport Protocol in Proxy mode (the framework, multi-hop version) |
| tcp-bbr    | TCP with bbr congestion control algorithm                                          |
| btp-next   | BATS™ protocol (the API/SDK, end-to-end version)                                   |
| brtp-next  | BATS™ protocol (the API/SDK, end-to-end version)                                   |
| tcp-next   | The tcp protocol integrated in bats protocol API/SDK, it's a TCP over TCP.         |
| KCP        | KCP Protocol       (uses KCP-TUN)                                                  |

### 1.1 BATS Protocol

The items `BTP`, `BRTP`,`BRTP_PROXY` are part of the BATS™ protocol. You can find the details in [BATS™](../bats/README.md).

### 1.2 KCP

[KCP](https://github.com/skywind3000/kcp) is a fast and reliable protocol that can reduce average latency by 30% to 40% and maximum delay by a factor of three, at the cost of 10% to 20% more bandwidth usage compared to TCP.

[KCP-TUN](https://github.com/xtaci/kcptun) is a practical application based on KCP. It uses Reed-Solomon Codes to recover lost packets

## 2. Tools

Oasis currently supports the following test tools:

| Tools                | Description                                            | Name in YAML |
| -------------------- | ------------------------------------------------------ | ------------ |
| ping                 | tool of sending ICMP messages                          | ping         |
| Iperf3               | tool of perform throughput test with UDP/TCP           | iperf        |
| tcp_message_endpoint | tool of sending/echoing TCP messages                   | rtt          |
| sshping              | tool of sending ping messages over SSH                 | sshping      |
| scp                  | tool of testing file transfer over different protocols | scp          |

### 2.1 TCP messaging endpoint

The binary located in `bin/tcp_message/tcp_endpoint` is a tool for measuring the RTT of TCP messages over other protocols. Its source code is in [bats-documentation](https://github.com/n-hop/bats-documentation).

### 2.3 sshping

`sshping` is a tool for sending ping messages over SSH. The source code is in [sshping](https://github.com/spook/sshping).

### 2.4 Traffic control (tc)

[`docs/tc-strategy.md`](tc-strategy.md) provides a detailed explanation of the traffic control strategy in Oasis.
