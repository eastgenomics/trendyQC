#!/bin/bash

if [[ ! -d "/app/trendyqc/grafana" ]]; then
    mkdir -p /app/trendyqc/grafana
fi

if [[ -f "/app/trendyqc/grafana/trendyqc.prom" ]]; then
    rm /app/trendyqc/grafana/trendyqc.prom
fi

echo "TrendyQC_cronjob_completed - $(date +'%Y/%m/%d %T')" > /app/trendyqc/grafana/trendyqc.prom