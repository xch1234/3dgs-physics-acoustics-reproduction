#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
test -f "$project/outputs/ficus_reconstruction/metrics.json"
exec bash "$project/code/run_official_linux.sh" \
  --model "$project/outputs/ficus_reconstruction" \
  --config "$project/code/PhysGaussian/config/ficus_config.json" \
  --tag ficus_reconstructed_full
