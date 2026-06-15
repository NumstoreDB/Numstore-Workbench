#!/usr/bin/env python3
import subprocess
import itertools
import os
import sys

program     = "./build/performance/big_file_inner_insert/big_file_inner_insert"
output_path = "performance/big_file_inner_insert/results/trials2.csv"

# 4096 (2^12) to 20 GiB (2^34 = 17 GiB, 2^35 = 34 GiB — round up to 2^34 is closest ≤20 GiB)
# 20 GiB = 21_474_836_480, so max power where 2^p <= 20*1024^3 is p=34 (17,179,869,184)
# Evenly spaced exponents → logarithmic spacing in byte values
file_size_powers  = list(range(12, 35, 4))   # 2^12 to 2^34, step 2  (~4 KiB to ~17 GiB)
insert_size_powers = list(range(12, 34, 4))  # 2^12 to 2^33, step 2  (~4 KiB to ~8 GiB)
offset_powers     = list(range(12, 35, 4))   # same range as file sizes; filtered to < fsize below

chunk_size = 4096

# Actual byte values
file_sizes   = [2**p for p in file_size_powers]
insert_sizes = [2**p for p in insert_size_powers]
offsets      = [2**p for p in offset_powers]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
first = True
with open(output_path, "w") as csv_file:
    for (fi, fsize), (oi, ofst), (ii, insize) in itertools.product(
            enumerate(file_sizes), enumerate(offsets), enumerate(insert_sizes)):
        print(f"{fi+1}/{len(file_sizes)}, {oi+1}/{len(offsets)}, {ii+1}/{len(insert_sizes)}")
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
