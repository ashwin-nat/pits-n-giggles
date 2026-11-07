# .pngt format changelog

Each section is a `header.json` `version`. Additive changes are listed under the
version they landed in; see the versioning policy in [README.md](README.md).

## Version 1

- `session.json`: added `player_index`, `sector_starts_m` (`[sector 2 start, sector 3 start]`, metres) and
  `ers_max_capacity_j`; `laps.json`: added `sector_ends_ms` (`[sector 1 end, sector 2 end]`, ms). All nullable, absent in older files.

- `session.json`: added `track_length_m` (metres, `null` when unknown). Absent in older
  files and read as `None`.

- `laps.json`: added `start_distance_m`, `end_distance_m`, `max_gap_m` (metres past the
  line covered by the lap's `lap_distance` samples; `null` when nothing was recorded past
  it). Absent in older files and read as `None`; consumers measure the lap instead.

- Initial format.
- `laps.json`: added `ers_harvest_limit_j` (joules, `null` outside F1). Absent in
  older (beta) files and read as `None`.
