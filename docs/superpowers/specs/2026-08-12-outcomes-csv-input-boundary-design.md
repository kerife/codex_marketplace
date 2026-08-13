# Outcomes CSV input boundary

## Goal

Make the career-outcomes CLI fail closed for candidate-supplied CSV paths
without changing its deterministic JSON output contract.

## Design

`read_rows` will reuse the shared descriptor-anchored `read_bounded_bytes`
loader with a 256 KiB limit, decode the bounded bytes as UTF-8 with BOM support,
and parse them through `csv.DictReader` over an in-memory text buffer. This
rejects direct and intermediate symlinks, devices, non-regular files, and
oversized inputs before CSV parsing. Existing row/date/consent validation stays
unchanged.

The CLI maps loader failures to stable JSON errors: unavailable input,
symlinked input, oversized input, or invalid UTF-8. It continues to return 0
for valid summaries, 2 for invalid input, writes no stdout on errors, and never
emits a traceback.

## TDD acceptance

- A regular canonical fixture still produces the existing summary.
- A symlink to a device or external CSV is rejected without following it.
- A valid CSV above 256 KiB is rejected before parsing.
- Invalid UTF-8 returns a deterministic JSON error without a traceback.
- Existing malformed-row, date, candidate-isolation, and warning contracts stay
  green.
