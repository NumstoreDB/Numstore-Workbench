#!/usr/bin/env python3
import subprocess
import itertools
import os
import sys

program     = "./build/performance/inner_insert/scripts/inner_insert"
output_path = "performance/inner_insert/results/trials.csv"

file_size_powers  = list(range(34, 12, 4))  
insert_size_powers = list(range(34, 12, 4))  
offset_powers     = list(range(34, 12, 4)) 

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
        args = [program, str(fsize), str(ofst), str(insize), str(chunk_size), "--csv", "--fallocate", "--buffered", "--smartfiles", "--unbuffered"]
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
