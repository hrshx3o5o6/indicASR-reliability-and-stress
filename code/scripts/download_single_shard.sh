#!/usr/bin/env bash
set -euo pipefail

url=${1:?usage: download_single_shard.sh URL OUTPUT EXPECTED_BYTES}
output=${2:?usage: download_single_shard.sh URL OUTPUT EXPECTED_BYTES}
expected=${3:?usage: download_single_shard.sh URL OUTPUT EXPECTED_BYTES}
token=${HF_TOKEN:?HF_TOKEN must be set}

mkdir -p "$(dirname "$output")"
while :; do
  current=0
  [ -f "$output" ] && current=$(stat -f%z "$output")
  [ "$current" -eq "$expected" ] && break
  [ "$current" -lt "$expected" ] || { echo "oversized download: $current/$expected" >&2; exit 2; }
  curl --fail --location --retry 5 --retry-delay 2 --continue-at - \
    --max-time 900 --speed-limit 10240 --speed-time 30 --silent --show-error \
    -H "Authorization: Bearer $token" "$url" -o "$output"
done
echo "downloaded $output ($(stat -f%z "$output") bytes)"
