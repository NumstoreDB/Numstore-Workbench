/*
 * CAUTION: This is not error handled (benchmark scaffollding only).
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
#include <unistd.h>  /* copy_file_range(), pread(), pwrite(), ftruncate() */

#include "inner_insert.h"
#include "csx_assert.h"
#include "error.h"
#include "os.h"
#include "smartfiles.h"
#include "stdtypes.h"

/******************************************************************************
 * SECTION: Printing
 * ----------------------------------------------------------------------------
 *
 * @brief Utility Functions for printing 
 ******************************************************************************/


void
print_csv_header (void)
{
  printf (
      "Method,Time (ms),Memory (KiB),File Size (KiB),Offset (KiB),"
      "Insert Size (KiB),Chunk Size (KiB)\n"
  );
}

void
print_csv (
    const struct bench_result *results,
    int                        count,
    const struct bench_params *p
)
{
  for (int i = 0; i < count; i++)
  {
    printf (
        "%s,%.6f,%.3f,%.3f,%.3f,%.3f,%.3f\n",
        results[i].label,
        results[i].time_ms,
        results[i].mem_b,
        KiB(p->fsize),
        KiB(p->ofst),
        KiB(p->insize),
        KiB(p->chunk_size)
    );
  }
}

void
print_friendly (
    const struct bench_result *results,
    int                        count,
    const struct bench_params *p
)
{
  printf (
      "%-20s  %s  %s\n",
      "",
      "Time (ms)    ",
      "Memory (KiB)  "
  );
  printf (
      "%-20s  %s  %s\n",
      "--------------------",
      "-------------",
      "-------------"
  );

  for (int i = 0; i < count; i++)
  {
    printf (
        "%-20s  %-13.3f  %-13.3f\n",
        results[i].label,
        results[i].time_ms,
        results[i].mem_b
    );
  }

  printf ("\n");
  printf ("  File size  : %.3f KiB\n", KiB(p->fsize ));
  printf ("  Offset     : %.3f KiB\n", KiB(p->ofst ));
  printf ("  Insert size: %.3f KiB\n", KiB(p->insize ));
  printf ("  Chunk size : %.3f KiB\n", KiB(p->chunk_size ));
}

/******************************************************************************
 * SECTION: Unbuffered
 * ----------------------------------------------------------------------------
 *
 * @brief One big malloc for the data to insert
 ******************************************************************************/


static void
unbuffered_timed_portion (
    i_file              *fp,
    const struct bench_params *p,
    const unsigned char *insert,
    unsigned char       *tail,
    error               *e
)
{
  i_pread_all_expect (fp, tail, p->fsize - p->ofst, p->ofst, e);
  i_pwrite_all (fp, tail, p->fsize - p->ofst, p->ofst + p->insize, e);
  i_pwrite_all (fp, insert, p->insize, p->ofst, e);
  i_fsync (fp, e);
}


double
bench_unbuffered (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
)
{
  const char filename[] = "temp_data.bin";

  i_file fp;
  i_touch (filename, e);
  i_open_rw (&fp, filename, e);
  i_pwrite_all (&fp, seed, p->fsize, 0, e);
  i_fsync (&fp, e);

  unsigned char *tail = malloc (p->fsize - p->ofst);
  ASSERT (tail);

  i_timer timer;
  i_timer_create (&timer, e);
  u64 start = i_timer_now_ns (&timer);

  unbuffered_timed_portion (&fp, p, insert, tail, e);

  u64 end = i_timer_now_ns (&timer);
  ASSERT (end >= start);

  i_close (&fp, e);
  i_remove_quiet (filename, e);
  free (tail);

  return (double)(end - start) / 1e6;
}

/******************************************************************************
 * SECTION: Buffered
 * ----------------------------------------------------------------------------
 *
 * @brief A fixed sized write block and a bunch of little writes / read
 ******************************************************************************/


static void
buffered_timed_portion (
    i_file              *fp,
    const struct bench_params *p,
    const unsigned char *insert,
    unsigned char       *buffer,
    error               *e
)
{
  u64 remaining = p->fsize - p->ofst;
  u64 read_pos  = p->fsize;

  /* Read back-to-front so the shift never clobbers pending source data */
  while (remaining > 0)
  {
    const u64 chunk = remaining < p->chunk_size ? remaining : p->chunk_size;
    read_pos -= chunk;

    i_pread_all_expect (fp, buffer, chunk, read_pos, e);
    i_pwrite_all (fp, buffer, chunk, read_pos + p->insize, e);

    remaining -= chunk;
  }

  i_pwrite_all (fp, insert, p->insize, p->ofst, e);
  i_fsync (fp, e);
}


double
bench_buffered (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
)
{
  const char filename[] = "temp_data.bin";

  i_file fp;
  i_touch (filename, e);
  i_open_rw (&fp, filename, e);
  i_pwrite_all (&fp, seed, p->fsize, 0, e);
  i_fsync (&fp, e);

  unsigned char *buffer = malloc (p->chunk_size);
  ASSERT (buffer);

  i_timer timer;
  i_timer_create (&timer, e);
  u64 start = i_timer_now_ns (&timer);

  buffered_timed_portion (&fp, p, insert, buffer, e);

  u64 end = i_timer_now_ns (&timer);
  ASSERT (end >= start);

  i_close (&fp, e);
  i_remove_quiet (filename, e);
  free (buffer);

  return (double)(end - start) / 1e6;
}

#ifdef __linux__

/******************************************************************************
 * SECTION: fallocate 
 * ----------------------------------------------------------------------------
 *
 * @brief Uses fallocate FALLOC_FL_INSERT_RANGE Only works on linux
 ******************************************************************************/


static void
fallocate_timed_portion (
    i_file              *fp,
    const struct bench_params *p,
    const unsigned char *insert,
    error               *e
)
{
  /*
   * Numstore doesn't support fallocate inner inserts
   * so I'll reach inside the file to get the fd. This
   * is only linux anyways.
   *
   * Obviously not the best software engineer practice, but
   * that's ok
   *
   * This is easy to fail - e.g. wrong block sizes etc
   * so I'll add error handling here only
   */
  if (fallocate (fp->fd, FALLOC_FL_INSERT_RANGE, (off_t)p->ofst, (off_t)p->insize))
  {
    perror ("fallocate(FALLOC_FL_INSERT_RANGE)");
    abort ();
  }

  i_pwrite_all (fp, insert, p->insize, p->ofst, e);
  i_fsync (fp, e);
}

double
bench_fallocate (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
)
{
  const char filename[] = "temp_data.bin";

  i_file fp;
  i_touch (filename, e);
  i_open_rw (&fp, filename, e);
  i_pwrite_all (&fp, seed, p->fsize, 0, e);
  i_fsync (&fp, e);

  /*
   * On all systems I tested with, you needed
   * both offset and insert size to be a multiple
   * of block size.
   *
   * I'm sure there are some exceptions but
   * ext4 is the big one so I'll keep this
   */

  i_timer timer;
  i_timer_create (&timer, e);
  u64 start = i_timer_now_ns (&timer);

  fallocate_timed_portion (&fp, p, insert, e);

  u64 end = i_timer_now_ns (&timer);
  ASSERT (end >= start);

  i_close (&fp, e);
  i_remove_quiet (filename, e);

  return (double)(end - start) / 1e6;
}
#endif

/******************************************************************************
 * SECTION: Smart Files
 * ----------------------------------------------------------------------------
 *
 * @brief Smart files implementation
 ******************************************************************************/


static void
smartfiles_timed_portion (
    smfile_t            *file,
    const struct bench_params *p,
    const unsigned char *insert
)
{
  smfile_insert (file, insert, p->ofst, p->insize);
}



double
bench_smartfiles (
    const unsigned char *seed,
    const unsigned char *insert,
    const struct bench_params *p,
    error *e
)
{
  const char filename[] = "temp_data.bin";

  smfile_t *file = smfile_open (filename);
  smfile_insert (file, seed, 0, p->fsize);

  i_timer timer;
  i_timer_create (&timer, e);
  u64 start = i_timer_now_ns (&timer);

  smartfiles_timed_portion (file, p, insert);

  u64 end = i_timer_now_ns (&timer);
  ASSERT (end >= start);

  smfile_close (file);
  i_remove_quiet (filename, e);

  return (double)(end - start) / 1e6;
}
