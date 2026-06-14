#!/usr/bin/env python3
import subprocess
import itertools
import os
import sys

program         = "./build/performance/big_file_inner_insert/big_file_inner_insert"
output_path     = "performance/big_file_inner_insert/results/trials.csv"

offsets         = [4096, 4096, 8192, 98304, 1_003_520, 10_002_432, 100_003_840, 1_000_013_824]
insert_sizes    = [4096, 4096, 4096, 8192, 98304, 1_003_520, 10_002_432, 100_003_840, 1_000_013_824]
file_sizes      = [102_400, 499_712, 999_424, 4_997_120, 9_998_336, 99_999_744, 999_997_440]

chunk_size      = 4096

os.makedirs(os.path.dirname(output_path), exist_ok=True)

first = True
with open(output_path, "w") as csv_file:
    for fsize, ofst, insize in itertools.product(file_sizes, offsets, insert_sizes):
        if ofst >= fsize:
            continue
        args = [program, str(fsize), str(ofst), str(insize), str(chunk_size), "--csv"]
        if first:
            args.append("--verbose")
            first = False
        result = subprocess.run(args, capture_output=True, text=True)
        if result.stdout:
            sys.stdout.write(result.stdout)
            sys.stdout.flush()
            csv_file.write(result.stdout)
            csv_file.flush()
        if result.stderr:
            sys.stderr.write(result.stderr)
            sys.stderr.flush()
