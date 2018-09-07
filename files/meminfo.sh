#!/bin/bash

HOSTNAME="${COLLECTD_HOSTNAME:-`hostname -f`}"
INTERVAL="${COLLECTD_INTERVAL:-10}"

while sleep "$INTERVAL"
do
    cat /proc/meminfo | sed -r -n 's/(.*):[ ]*(.+) kB/\1 \2/p' | awk -v hn=$HOSTNAME -v interval=$INTERVAL '/.*/ { printf("PUTVAL %s/meminfo/memory-%s interval=%s N:%s\n", hn, $1, interval, ($2 * 1024)) }'
done