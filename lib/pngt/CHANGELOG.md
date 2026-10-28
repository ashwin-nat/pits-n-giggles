# .pngt format changelog

Each section is a `header.json` `version`. Additive changes are listed under the
version they landed in; see the versioning policy in [README.md](README.md).

## Version 1

- Initial format.
- `laps.json`: added `ers_harvest_limit_j` (joules, `null` outside F1). Absent in
  older (beta) files and read as `None`.
