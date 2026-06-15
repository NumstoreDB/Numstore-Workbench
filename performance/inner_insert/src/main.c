#include "inner_insert.h"

int
main (int argc, char **argv)
{
  /*
   * Parse Arguments
   *
   * Takes in
   *  File Size   - Initial File size before inner insert
   *  Offset      - Which offset to insert data into
   *  Insert Size - The size of the packet to insert in the middle
   *  Chunk Size  - Size of each chunk in the buffered approach
   *
   * Flags (optional, any order):
   *  --unbuffered  - run unbuffered benchmark
   *  --buffered    - run buffered benchmark
   *  --fallocate   - run fallocate benchmark
   *  --smartfiles  - run smartfiles benchmark
   *  --verbose     - print header; otherwise just data
   *
   *  No method flags = run all four
   */
  if (argc < 5)
  {
    fprintf (
        stdout,
        "Usage: big_file_inner_insert <FILE SIZE> <OFFSET> <INSERT SIZE> "
        "<CHUNK SIZE> [--unbuffered] [--buffered] [--fallocate] "
        "[--smartfiles] [--verbose]\n"
    );
    return EXIT_FAILURE;
  }

  struct bench_params p = {
    .fsize      = (u64)strtoull (argv[1], NULL, 10),
    .ofst       = (u64)strtoull (argv[2], NULL, 10),
    .insize     = (u64)strtoull (argv[3], NULL, 10),
    .chunk_size = (u64)strtoull (argv[4], NULL, 10),
  };

  int run_unbuffered = 0;
  int run_buffered   = 0;
  int run_fallocate  = 0;
  int run_smartfiles = 0;
  int verbose        = 0;
  int csv            = 0;
  for (int i = 5; i < argc; i++)
  {
    if      (strncmp (argv[i], "--unbuffered", 12) == 0) run_unbuffered = 1;
    else if (strncmp (argv[i], "--buffered",   10) == 0) run_buffered   = 1;
    else if (strncmp (argv[i], "--fallocate",  11) == 0) run_fallocate  = 1;
    else if (strncmp (argv[i], "--smartfiles", 12) == 0) run_smartfiles = 1;
    else if (strncmp (argv[i], "--verbose",     9) == 0) verbose        = 1;
    else if (strncmp (argv[i], "--csv",         5) == 0) csv            = 1;
    else
    {
      fprintf (stderr, "Unknown flag: %s\n", argv[i]);
      return EXIT_FAILURE;
    }
  }

  /* No method flags = run all */
  if (!run_unbuffered && !run_buffered && !run_fallocate && !run_smartfiles)
  {
    run_unbuffered = run_buffered = run_fallocate = run_smartfiles = 1;
  }

  /*
   * Sanitization:
   *  - Offset must be less than file size
   *  - Chunk must be greater than 0
   */
  if (p.ofst > p.fsize)
  {
    fprintf (
        stderr,
        "offset %" PRIu64 " exceeds file size %" PRIu64 "\n",
        p.ofst,
        p.fsize
    );
    return EXIT_FAILURE;
  }

  if (p.chunk_size == 0)
  {
    fprintf (stderr, "chunk size must be > 0\n");
    return EXIT_FAILURE;
  }

  /*
   * Allocate memory and initialize data
   *  seed   - the original file contents
   *  insert - the data to insert
   */
  unsigned char *seed   = malloc (p.fsize);
  unsigned char *insert = malloc (p.insize);
  ASSERT (seed && insert);

  for (u64 i = 0; i < p.fsize; i++)
    seed[i] = (unsigned char)(i % 256);
  for (u64 i = 0; i < p.insize; i++)
    insert[i] = (unsigned char)(i % 256);

  error e = error_create ();

  struct bench_result results[4];
  int                 count = 0;

  if (run_unbuffered)
  {
    results[count].label  = "unbuffered";
    results[count].mem_b = KiB((p.fsize - p.ofst + p.insize) ) ;
    results[count].time_ms = bench_unbuffered (seed, insert, &p, &e);
    count++;
  }

  if (run_buffered)
  {
    results[count].label  = "buffered";
    results[count].mem_b = KiB((p.chunk_size + p.insize) ) ;
    results[count].time_ms = bench_buffered (seed, insert, &p, &e);
    count++;
  }

  if (run_fallocate)
  {
#ifdef __linux__
    results[count].label  = "fallocate";
    results[count].mem_b = KiB(p.insize);
    results[count].time_ms = bench_fallocate (seed, insert, &p, &e);
    count++;
#else 
    fprintf(stderr, "Fallocate version not supported on your machine. Need Linux\n");
    abort();
#endif
  }

  if (run_smartfiles)
  {
    results[count].label  = "smartfiles";
    results[count].mem_b = KiB(p.insize);
    results[count].time_ms = bench_smartfiles (seed, insert, &p, &e);
    count++;
  }

  free (insert);
  free (seed);

  if (!verbose && !csv)
  {
    fprintf (stderr, "error: specify --verbose or --csv\n");
    return EXIT_FAILURE;
  }
  if (verbose && !csv)
  {
    print_friendly (results, count, &p);
  }
  else if (csv)
  {
    if (verbose) print_csv_header ();
    print_csv (results, count, &p);
  }

  return 0;
}
