/*
 * CAUTION: This is not error handled (benchmark scaffolding only).
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE /* fallocate, FALLOC_FL_INSERT_RANGE, copy_file_range */
#endif

#include <fcntl.h>   /* fallocate(), FALLOC_FL_INSERT_RANGE */
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/vfs.h> /* fstatfs(), struct statfs */
#include <unistd.h>  /* copy_file_range(), pread(), pwrite(), ftruncate() */

#include "csx_assert.h"
#include "error.h"
#include "os.h"
#include "smartfiles.h"
#include "stdtypes.h"

#define KiB(bytes) ((bytes) / 1024.0)

struct bench_params
{
  u64 fsize;
  u64 ofst;
  u64 insize;
  u64 chunk_size;
};

struct bench_result
{
  const char *label;
  double      time_ms;
  double      mem_b;
};

void
print_csv_header (void);

void
print_csv (
    const struct bench_result *results,
    int                        count,
    const struct bench_params *p
);

void
print_friendly (
    const struct bench_result *results,
    int                        count,
    const struct bench_params *p
);

double
bench_unbuffered (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
);

double
bench_buffered (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
);

double
bench_optimized (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
);

double
bench_smartfiles (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
);

