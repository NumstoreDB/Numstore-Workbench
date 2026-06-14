#!/usr/bin/env bash
set -euo pipefail

BINARY="./build/performance/big_file_inner_insert/big_file_inner_insert"
PARAMS="100000000 4096 4096 4096"
FLAMEGRAPH_DIR="./thirdparty/FlameGraph"

METHODS=("unbuffered" "buffered" "optimized" "smartfiles")

for method in "${METHODS[@]}"; do
  OUTPUT="./performance/big_file_inner_insert/results/flamegraph_${method}.svg"

  echo "Recording perf data for ${method}..."
  sudo perf record \
    -F 999 \
    -g \
    --call-graph dwarf \
    -e cycles \
    -o "perf_${method}.data" \
    -- $BINARY $PARAMS --${method} --verbose

  echo "Generating flame graph for ${method}..."
  sudo perf script -i "perf_${method}.data" \
    | "$FLAMEGRAPH_DIR/stackcollapse-perf.pl" --kernel \
    | "$FLAMEGRAPH_DIR/flamegraph.pl" \
        --title "big_file_inner_insert: ${method}" \
        --width 1600 \
        --color java \
    > "$OUTPUT"

  echo "Done: $OUTPUT"

  sudo rm -rf *.data 
  sudo rm -rf *.old
done
