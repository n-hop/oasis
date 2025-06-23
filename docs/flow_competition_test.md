## The complex topology

The required topology for flow competition test is as follows:

```text
[h0]    ---------competition flow -----\
[h1]    ---------competition flow -----\
                                       |
[target protocol sender]       ---------------[Router]--------------- >    [target protocol receiver]
                                       |
                                       \-------------> [h0']
                                       \-------------> [h1']
```

The test case configuration is as follows:

```yaml
tests:
  test1:
    description: "Flow competition test with multiple protocols"
    topology:
      config_name: complex_mesh_net
      config_file: predefined.topology.yaml
    target_protocols: [tcp-bbr]
    route: static_bfs
    test_tools:
      iperf:
        interval: 1
        interval_num: 10
        packet_type: tcp
        client_host: 1
        server_host: 6
      competition_flow:
        - flow_type: tcp # competition flow from `h0` to `h5` in random joining and leaving
          client_host: 0
          server_host: 5
        - flow_type: tcp # competition flow from `h1` to `h6` in random joining and leaving
          client_host: 1
          server_host: 6
```

The example configuration is at `src/config/protocol-flow-competition-test.yaml`.


**Node mapping:**

- 0: h0
- 1: h1
- 2: target protocol sender
- 3: Router
- 4: target protocol receiver
- 5: h0'
- 6: h1'

**Connections:**

- h0 (0) → Router (3)
- h1 (1) → Router (3)
- target protocol sender (2) → Router (3)
- Router (3) → target protocol receiver (4)
- Router (3) → h0' (5)
- Router (3) → h1' (6)

**Adjacency matrix (7x7):**

```yaml
matrix_data:
   # 0  1  2  3  4  5  6
  - [0, 0, 0, 1, 0, 0, 0]  # 0: h0
  - [0, 0, 0, 1, 0, 0, 0]  # 1: h1
  - [0, 0, 0, 1, 0, 0, 0]  # 2: target protocol sender
  - [1, 1, 1, 0, 1, 1, 1]  # 3: router
  - [0, 0, 0, 1, 0, 0, 0]  # 4: target protocol receiver
  - [0, 0, 0, 1, 0, 0, 0]  # 5: h0'
  - [0, 0, 0, 1, 0, 0, 0]  # 6: h1'
```

**Legend:**  

- Each row is a node, each column is a node.
- A `1` at `[i][j]` means a directed edge from node `i` to node `j`.

**Bandwidths:**

Fixed 1000 Mbps for all links.

**Delay:**

Fixed 10 ms for all links.

**loss rate:**

The links which are connected to the router have a loss rate of 3% for each direction.
