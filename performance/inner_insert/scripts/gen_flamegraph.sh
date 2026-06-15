#!/usr/bin/env bash
set -euo pipefail

BINARY="./build/performance/inner_insert/inner_insert"
PARAMS="100000000 4096 4096 4096"
FLAMEGRAPH_DIR="./thirdparty/FlameGraph"
METHODS=("unbuffered" "buffered" "fallocate" "smartfiles")

OS="$(uname -s)"

require_tool() {
  if ! command -v "$1" &>/dev/null; then
    echo "ERROR: '$1' not found. $2" >&2
    exit 1
  fi
}

case "$OS" in
  Linux)
    require_tool perf "Install with: sudo apt install linux-perf (or linux-tools-$(uname -r))"
    PROFILER=perf
    ;;
  Darwin)
    require_tool dtrace "DTrace ships with macOS; run: sudo DevToolsSecurity -enable"
    PROFILER=dtrace
    ;;
  *)
    echo "ERROR: Unsupported OS: $OS" >&2
    exit 1
    ;;
esac

require_tool perl "Install with your package manager (e.g. brew install perl)"

[[ -f "$FLAMEGRAPH_DIR/flamegraph.pl" ]] || {
  echo "ERROR: FlameGraph scripts not found at $FLAMEGRAPH_DIR" >&2
  exit 1
}

flamegraph_render() {
  local method="$1"
  "$FLAMEGRAPH_DIR/flamegraph.pl" \
    --title "inner_insert: ${method}" \
    --width 1600 \
    --color java
}

profile_linux() {
  local method="$1" output="$2" datafile="perf_${method}.data"

  echo "  [perf] recording..."
  sudo perf record \
    -F 999 \
    -g \
    --call-graph dwarf \
    -e cycles \
    -o "$datafile" \
    -- $BINARY $PARAMS --${method} --verbose

  echo "  [perf] generating flame graph..."
  sudo perf script -i "$datafile" \
    | "$FLAMEGRAPH_DIR/stackcollapse-perf.pl" --kernel \
    | flamegraph_render "$method" \
    > "$output"

  sudo rm -f "$datafile" "${datafile}.old"
}

profile_darwin() {
  local method="$1" output="$2" datafile="dtrace_${method}.stacks"

  # Estimate a duration from a test run, or use a generous fixed cap.
  # DTrace self-terminates via tick-Xs so we don't need to background the binary.
  # profile-97 /pid == $target/ captures user stacks including time spent in-kernel.
  local duration=120   # seconds; adjust if runs are reliably shorter/longer

  echo "  [dtrace] recording (up to ${duration}s, stops when binary exits)..."

  # Launch binary, grab its PID, then let dtrace attach and self-exit
  # when either the tick fires or the process ends (whichever is first).
  $BINARY $PARAMS --${method} --verbose &
  local target_pid=$!

  sudo dtrace \
    -x ustackframes=100 \
    -n "profile-97 /pid == ${target_pid}/ { @[ustack()] = count(); }
        tick-${duration}s { exit(0); }" \
    -o "$datafile" || true   # exits non-zero when target process ends — that's fine

  wait "$target_pid" 2>/dev/null || true

  echo "  [dtrace] generating flame graph..."
  # stackcollapse.pl is the correct folder for DTrace output (not stackcollapse-dtrace.pl)
  "$FLAMEGRAPH_DIR/stackcollapse.pl" "$datafile" \
    | flamegraph_render "$method" \
    > "$output"

  rm -f "$datafile"
}

mkdir -p "./performance/inner_insert/results"

for method in "${METHODS[@]}"; do
  OUTPUT="./performance/inner_insert/results/flamegraph_${method}.svg"
  echo "Profiling [${method}] on ${OS} using ${PROFILER}..."

  case "$PROFILER" in
    perf)   profile_linux  "$method" "$OUTPUT" ;;
    dtrace) profile_darwin "$method" "$OUTPUT" ;;
  esac

  echo "Done: $OUTPUT"
done
