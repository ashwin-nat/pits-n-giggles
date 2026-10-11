---
description: Re-measure per-sensor compressed size from .pngt recordings and update the Lap Analyzer entropy classes
allowed-tools: Read, Edit, Grep, Glob, Bash
---

Recalibrate the entropy class of each Lap Analyzer sensor against real recordings. The classes
drive the size estimate on the Lap Analyzer settings page.

Never commit. Show the diff and stop for sign-off.

## Steps

1. **Input**: a `.pngt` file or a directory, defaulting to `data/`. Tell the user a recording
   made with a subset of sensors cannot measure the unrecorded ones. The best input is replays
   recorded with the Advanced preset.
2. Run `poetry run python -m apps.dev_tools.pngt_sensor_stats --dir <path> --json` (or `--file`).
   A full `data/` takes about 40 seconds.
3. Map each `.pngt` key to its config field through `F1_SENSORS` in
   `apps/backend/state_mgmt_layer/data_per_driver/telemetry_recorder/telemetry_recorder.py`.
   It is the only place the mapping exists (e.g. key `tyre_wear.fl` is field `tyre_wear_fl`).
   Keys in the data with no entry there are old or removed sensors: report them, ignore them.
4. In `lib/config/schema/lap_analyzer.py`, set each field's `sensor_field(entropy=...)` to the
   measured `entropy_class`. A field whose key is missing from the data is left alone and reported.
5. Report drift:
   - per class, the mean measured B/sample of its member sensors against the
     `ENTROPY_BYTES_PER_SAMPLE` coefficient
   - `lap_distance` + `lap_time_ms` B/sample against `MANDATORY_BYTES_PER_SAMPLE`
   - the sum check: sum of class values for the recorded sensors + mandatory, against the
     measured `bytes_per_row` (whole-file bytes, so slightly higher from metadata)

   **Only change `ENTROPY_BYTES_PER_SAMPLE` / `MANDATORY_BYTES_PER_SAMPLE` when the user confirms.**
6. Run `poetry run pytest tests/tests_config -k lap_analyzer`, show the diff, and stop.

## Notes

- Files from different versions can carry different manifests; the tool flags those keys with `*`
  and `manifest_differs`. That is expected for old recordings and not a reason to stop.
- Class assignment is nearest-in-log-space, so a sensor near a boundary can flip between runs on
  different data. Mention borderline sensors rather than silently flipping them.
