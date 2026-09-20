#!/usr/bin/env bash
set -euo pipefail

raw_dir=${1:?usage: download_fleurs_shards.sh RAW_DIR}
token=${HF_TOKEN:?HF_TOKEN must be set}
base_url='https://huggingface.co/datasets/google/fleurs/resolve/main/parquet-data'
parallelism=${FLEURS_PARALLELISM:-8}
chunk_size=${FLEURS_CHUNK_SIZE:-67108864}

size_for() {
  case "$1" in
    hi_in) echo 161992910 ;;
    ta_in) echo 288019911 ;;
    te_in) echo 204572374 ;;
    ml_in) echo 386773831 ;;
    kn_in) echo 299080789 ;;
    ur_pk) echo 174091927 ;;
    *) return 1 ;;
  esac
}

mkdir -p "$raw_dir/.parts"

download_chunk() {
  local config=$1
  local start=$2
  local end=$3
  local part_dir="$raw_dir/.parts/$config"
  local part="$part_dir/$start-$end"
  local expected=$((end - start + 1))
  local have=0
  [ -f "$part" ] && have=$(stat -f%z "$part")
  [ "$have" -eq "$expected" ] && return 0
  rm -f "$part"
  mkdir -p "$part_dir"
  curl --fail --location --retry 5 --retry-delay 2 --silent --show-error \
    -H "Authorization: Bearer $token" \
    --range "$start-$end" \
    "$base_url/$config/validation-00000-of-00001.parquet" \
    -o "$part"
  have=$(stat -f%z "$part")
  [ "$have" -eq "$expected" ] || {
    echo "short chunk: $config $start-$end ($have/$expected)" >&2
    return 1
  }
}

for config in hi_in ta_in te_in ml_in kn_in ur_pk; do
  total=$(size_for "$config")
  part_dir="$raw_dir/.parts/$config"
  mkdir -p "$part_dir"
  pids=()
  for ((start=0; start<total; start+=chunk_size)); do
    end=$((start + chunk_size - 1))
    [ "$end" -lt "$total" ] || end=$((total - 1))
    download_chunk "$config" "$start" "$end" &
    pids+=("$!")
    while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$parallelism" ]; do
      sleep 1
    done
  done
  status=0
  for pid in "${pids[@]}"; do
    wait "$pid" || status=1
  done
  [ "$status" -eq 0 ] || exit "$status"
  output="$raw_dir/$config-validation.parquet"
  tmp="$output.tmp"
  : > "$tmp"
  for ((start=0; start<total; start+=chunk_size)); do
    end=$((start + chunk_size - 1))
    [ "$end" -lt "$total" ] || end=$((total - 1))
    cat "$part_dir/$start-$end" >> "$tmp"
  done
  [ "$(stat -f%z "$tmp")" -eq "$total" ] || exit 1
  mv "$tmp" "$output"
  echo "assembled $output ($(stat -f%z "$output") bytes)"
done
