#!/usr/bin/env bash
set -euo pipefail

FOLDER="performance/inner_insert/results"

if [[ ! -d "$FOLDER" ]]; then
    echo "Error: '$FOLDER' is not a directory"
    exit 1
fi

OUT="${2:-${FOLDER}.tar.gz}"

tar -czf "$OUT" "$FOLDER"
echo "Created: $OUT  ($(du -sh "$OUT" | cut -f1))"
