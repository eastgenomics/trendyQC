#!/bin/bash

if [[ ! -d "/app/trendyqc/grafana" ]]; then
    mkdir -p /app/trendyqc/grafana
fi

if [[ -f "/app/trendyqc/grafana/trendyqc.prom" ]]; then
    rm /app/trendyqc/grafana/trendyqc.prom
fi

echo "TrendyQC_cronjob_completed - $(date +%s)" > /app/trendyqc/grafana/trendyqc.prom