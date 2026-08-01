#!/bin/sh
# Pull (never delete) small diagnostic artifacts from an ephemeral worker.
# Usage: sync_remote_artifacts.sh HOST PORT REMOTE_DIR LOCAL_DIR [SECONDS]
set -eu

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  echo "usage: $0 HOST PORT REMOTE_DIR LOCAL_DIR [SECONDS]" >&2
  exit 64
fi

host=$1
port=$2
remote_dir=$3
local_dir=$4
interval=${5:-0}

mkdir -p "$local_dir"

sync_once() {
  rsync --archive --partial --prune-empty-dirs \
    --exclude '.git/' --exclude '__pycache__/' --exclude '*.tmp' \
    -e "ssh -o BatchMode=yes -p $port" \
    "root@$host:$remote_dir/" "$local_dir/"
}

if [ "$interval" -eq 0 ]; then
  sync_once
  exit 0
fi

while :; do
  sync_once
  sleep "$interval"
done
