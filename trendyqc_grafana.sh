#!/bin/bash

if [[ -f "/var/log/monitoring/trendyqc.prom" ]]; then
    rm /var/log/monitoring/trendyqc.prom
fi

echo "TrendyQC_cronjob_completed - $(date +'%Y/%m/%d %T')" > /var/log/monitoring/trendyqc.prom