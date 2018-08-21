#!/bin/bash

sudo tc qdisc del dev $1 root &> /dev/null
# echo "Ignore 'RTNETLINK answers: No such file or directory'"
sudo tc qdisc add dev $1 root netem delay $2  loss $3

