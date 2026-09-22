# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from dataclasses import dataclass
from typing import Optional, Union

from lib.pngt import (BaseTelemetrySnapshot, SensorConfig, SensorDtype,
                      SensorMapper, SensorType)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class _CatalogEntry:
    """One F1SensorMapper catalog row: everything needed to resolve a dotted sensor key
    against a real TelemetrySnapshot, plus everything needed to describe it in a
    manifest.json entry. field_name/dtype answer SensorMapper's own ABC contract
    (get_value()/get_dtype()); label/unit/sensor_type answer sensor_config(), the one
    extra method this concrete mapper adds beyond that ABC -- see its docstring."""
    field_name: str
    dtype: SensorDtype
    label: str
    unit: str
    sensor_type: SensorType


class F1SensorMapper(SensorMapper):
    """Concrete SensorMapper for the real (F1-domain-specific) TelemetrySnapshot defined
    in telemetry_recorder.py. Deliberately scoped to that class's current field set only
    -- the reduced set is sufficient for the beta; expanding TelemetrySnapshot to the
    full F1 sensor catalog (tyre temp/pressure/damage, brake temp, suspension, g-force,
    fuel, ...) is tracked separately and this mapper's catalog grows alongside it, not
    ahead of it.

    Dotted-key convention (see plans/telemetry_recording/phase-7-pr/implementation-plan.md's
    naming sketch, anchored against apps/lap-analyzer/src/lib/enumLabels.ts's existing
    "ers.deploy_mode" key): standalone scalars with no sibling fields stay flat
    (`speed`, `gear`, `throttle`, `brake`, `steering`, `clutch`, `engine_rpm`); fields
    with real siblings get a `group.field` or `group.corner` dotted key (`ers.*`,
    `tyre_wear.*`).

    `ers_deploy_mode` is stored on TelemetrySnapshot as a plain int (already `.value`d
    from lib.f1_types.packet_7_car_status_data.CarStatusData.ERSDeployMode by whatever
    converts a real packet into a TelemetrySnapshot -- not this mapper's job, and not
    redefined here since that F1BaseEnum already exists) -- see enumLabels.ts's
    "ers.deploy_mode": {0: "None", 1: "Medium", 2: "Hotlap", 3: "Overtake"} for how the
    frontend already resolves it.

    Known caveat, not fixed here: lib.pngt.dtypes's own missing-value sentinel for every
    integer SensorDtype is -1 (see missing_value()), which collides with `gear`'s own
    legitimate reverse-gear value of -1 -- a reversed lap and a gap in recording are
    indistinguishable in the exported data for this one sensor. This is a
    lib.pngt.ingest-level limitation (the sentinel is fixed regardless of INT8 vs INT16),
    not something a mapper's dtype choice can work around.
    """

    _CATALOG: dict[str, _CatalogEntry] = {
        "throttle": _CatalogEntry("throttle", SensorDtype.FLOAT32, "Throttle", "%", SensorType.CONTINUOUS),
        "brake": _CatalogEntry("brake", SensorDtype.FLOAT32, "Brake", "%", SensorType.CONTINUOUS),
        "steering": _CatalogEntry("steering", SensorDtype.FLOAT32, "Steering", "", SensorType.CONTINUOUS),
        "clutch": _CatalogEntry("clutch", SensorDtype.FLOAT32, "Clutch", "%", SensorType.CONTINUOUS),
        "speed": _CatalogEntry("speed", SensorDtype.FLOAT32, "Speed", "km/h", SensorType.CONTINUOUS),
        "gear": _CatalogEntry("gear", SensorDtype.INT8, "Gear", "", SensorType.DISCRETE),
        "engine_rpm": _CatalogEntry("engine_rpm", SensorDtype.FLOAT32, "Engine RPM", "rpm", SensorType.CONTINUOUS),
        "ers.deploy_mode": _CatalogEntry("ers_deploy_mode", SensorDtype.INT8, "ERS Deploy Mode", "", SensorType.DISCRETE),
        "ers.store_energy": _CatalogEntry("ers_store_energy", SensorDtype.FLOAT32, "ERS Store Energy", "J", SensorType.CONTINUOUS),
        "tyre_wear.fl": _CatalogEntry("tyre_wear_fl", SensorDtype.FLOAT32, "Tyre Wear FL", "%", SensorType.CONTINUOUS),
        "tyre_wear.fr": _CatalogEntry("tyre_wear_fr", SensorDtype.FLOAT32, "Tyre Wear FR", "%", SensorType.CONTINUOUS),
        "tyre_wear.rl": _CatalogEntry("tyre_wear_rl", SensorDtype.FLOAT32, "Tyre Wear RL", "%", SensorType.CONTINUOUS),
        "tyre_wear.rr": _CatalogEntry("tyre_wear_rr", SensorDtype.FLOAT32, "Tyre Wear RR", "%", SensorType.CONTINUOUS),
    }

    def get_value(
        self,
        snapshot: BaseTelemetrySnapshot,
        sensor_key: str,
    ) -> Optional[Union[float, int]]:
        return getattr(snapshot, self._resolve(sensor_key).field_name)

    def get_dtype(self, sensor_key: str) -> SensorDtype:
        return self._resolve(sensor_key).dtype

    def sensor_config(self, sensor_key: str) -> SensorConfig:
        """Not part of the SensorMapper ABC -- the manifest.json fields (label/unit/
        SensorType) that get_value()/get_dtype() alone can't produce. Called once per
        configured sensor key when assembling write_session()'s `sensors` argument."""
        entry = self._resolve(sensor_key)
        return SensorConfig(key=sensor_key, label=entry.label, unit=entry.unit, type=entry.sensor_type)

    @classmethod
    def known_sensor_keys(cls) -> tuple[str, ...]:
        """Every dotted key this mapper can resolve -- the full catalog, independent of
        any particular TelemetryRecorderConfig's (user-selected) subset."""
        return tuple(cls._CATALOG)

    def _resolve(self, sensor_key: str) -> _CatalogEntry:
        try:
            return self._CATALOG[sensor_key]
        except KeyError as exc:
            raise KeyError(f"Unknown sensor key {sensor_key!r}") from exc
