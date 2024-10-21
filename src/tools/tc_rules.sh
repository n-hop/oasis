#!/bin/bash

# ################# Usage #################
# H0 (eth0)<-----------------> (eth0)H1
# `tc_rules.sh` is used to define the tc rules on the link between H0 and H1
# #########################################
# run `tc_rules.sh eth0 set` on host H0 to apply the tc rules:
# sudo ./tc_rules.sh eth0 set
# #########################################
# run `tc_rules.sh eth0 set` on host H1 to apply the tc rules:
# sudo ./tc_rules.sh eth0 set
# #########################################
# Unset the tc rules by running the following command:
# sudo ./tc_rules.sh eth0 unset

# step 0. get input interface name
if [ $# -ne 2 ]; then
    echo "Usage: $0 <interface_name> set"
    echo "Usage: $0 <interface_name> unset"
    exit 1
fi

applied_interface=$1
# check if interface exists
if [ ! -d "/sys/class/net/$applied_interface" ]; then
    echo "Interface $applied_interface does not exist"
    exit 1
fi

action_type=$2
if [ "$action_type" != "set" ] && [ "$action_type" != "unset" ]; then
    echo "Usage: $0 <interface_name> set"
    echo "Usage: $0 <interface_name> unset"
    exit 1
fi

# add tc rules
function setup_tc_rules {
    local interface=$1
    local bandwidth=$2
    local loss_rate=$3
    local delay=$4
    echo "Applying tc rules on interface: $interface with bandwidth: $bandwidth, loss_rate: $loss_rate, delay: $delay"

    # step 1.1: set bandwidth
    tc qdisc add dev "$interface" root handle 1: tbf rate "$bandwidth" burst 125.0kb latency 1ms

    # step 1.2: add ifb interface
    ip link add name ifb0 type ifb
    ip link set dev ifb0 up
    tc qdisc add dev "$interface" ingress
    tc filter add dev "$interface" parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0
    # check if delay is greater than 0
    if [ "$delay" -eq 0 ]; then
        echo "No delay is added"
        tc qdisc add dev ifb0 root netem loss "$loss_rate" limit 10000000
    else
        tc qdisc add dev ifb0 root netem loss "$loss_rate" delay "$delay"ms limit 30000000
    fi
}

# cleanup tc rules
function cleanup {
    echo "Cleaning up tc rules"
    local interface=$1
    if tc qdisc show dev "$interface" | grep -q "ingress"; then
        echo "Deleting tc ingress qdisc"
        tc qdisc del dev "$interface" ingress
    fi

    if tc filter show dev "$interface" parent ffff: | grep -q "mirred egress"; then
        echo "Deleting tc filter"
        tc filter del dev "$interface" parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0
    fi

    if [ -z "$(tc qdisc show dev "$interface" | grep "tbf 1")" ]; then
        echo "No tc rules found on interface $interface"
    else
        echo "Deleting tbf rate rules on interface $interface"
        tc qdisc del dev "$interface" root handle 1: tbf rate "$bandwidth" burst 125.0kb latency 1ms
    fi
    
    if [ -d "/sys/class/net/ifb0" ]; then
        echo "Deleting ifb0 interface"
        tc qdisc del dev ifb0 root
        ip link set dev ifb0 down
        ip link delete ifb0
    fi
}

# change the following values to set the desired bandwidth, loss rate, and delay
bandwidth=1000mbit
loss_rate=0%
delay=1 #ms

if [ "$action_type" == "set" ]; then
    setup_tc_rules "$applied_interface" "$bandwidth" "$loss_rate" "$delay"
else
    cleanup "$applied_interface"
fi