# Traffic control (tc)

## tc in Linux

In Linux, the traffic control for shaping the flow is implemented by the `tc` command. See details in [tc(8)](https://www.man7.org/linux/man-pages/man8/tc.8.html)

## shaping strategy in Oasis

<div align="center" style="text-align:center"> 
<img src="./imgs/Oasis-tc-strategy.svg" alt="tc strategy"></div>
<div align="center">Fig 1.1 Traffic shaping strategy</div>

## tc example

Target:

- Limit the rate from `h0` to `h1` to 100Mbit/s
- For direction `h1` to `h0`, add 5% packet loss, 10ms delay.

Topology:

```bash
h0 (eth0) --- (eth0) h1
```

on host `h0`, set the rate limit on `eth0`:

```bash
tc qdisc add dev eth0 root handle 5: tbf rate 100.0Mbit burst 150kb latency 1ms
```

on host `h1`, we create an `ifb` interface `ifb0`:

```bash
ip link add name ifb0 type ifb
ip link set ifb0 up
```

Then, redirect the ingress ip traffic from `eth0` to `ifb0`:

```bash
tc qdisc add dev eth0 ingress
tc filter add dev h1-eth0 parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0
```

Finally, apply the traffic shaping(loss, delay, jitter) on `ifb0`:

```bash
tc qdisc add dev ifb0 root netem loss 5% delay 10ms limit 20000000
```

In order to have a better simulation result for latency, a larger buffer/queue size is preferred(specified by `limit 20000000` in tc command) otherwise tc will drop more packets when buffer is overwhelmed.

## tc_rules script

`./src/tools/tc_rules.sh` can be used to apply or unset the above tc rules for a topology H0-H1.

```bash
# run `tc_rules.sh eth0 set` on host H0 to apply the tc rules:
sudo ./src/tools/tc_rules.sh eth0 set

# run `tc_rules.sh eth0 set` on host H1 to apply the tc rules:
sudo ./src/tools/tc_rules.sh eth0 set
```

To unset the rules, run:

```bash
sudo ./src/tools/tc_rules.sh eth0 unset
```