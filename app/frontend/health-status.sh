#!/bin/sh
set -eu

health_file=/tmp/frontend-health.json
started_at=$(date +%s)

write_health() {
  uptime_seconds=$(($(date +%s) - started_at))
  printf '{"status":"ok","service":"frontend","port":80,"uptime_seconds":%s}\n' \
    "$uptime_seconds" > "${health_file}.tmp"
  mv "${health_file}.tmp" "$health_file"
}

write_health
(
  while :; do
    sleep 1
    write_health
  done
) &