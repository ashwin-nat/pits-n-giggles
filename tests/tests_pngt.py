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
# pylint: skip-file

import dataclasses
import json
import os
import sys
import zipfile
from io import BytesIO

import numpy as np
import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.pngt import (CompletedLap, DriverExportData, DriverNotFoundError,
                      DriverRecord, InvalidHeaderError, InvalidManifestError,
                      LapMetadata, NotAZipFileError, SensorConfig,
                      SensorDtype, SensorType, SessionBest,
                      SessionMetadata, TrackInfo, UnsupportedFormatError,
                      UnsupportedVersionError, delete_laps, mark_lap_good,
                      read_driver_laps, read_header, read_lap_telemetry,
                      read_manifest, read_session, rename_session,
                      suggest_filename, write_session)

# ----------------------------------------------------------------------------------------------------------------------
# Fixtures
#
# Deliberately made-up, non-F1 sensor/driver/track names ("widget_speed", "gizmo.left.temp",
# "Test Driver A"/"Nullteam", "fakecircuit") rather than real F1 terms. This is a structural
# proof that lib/pngt carries zero embedded F1 domain knowledge -- using real sensor keys
# here could make a future reader mistake this for hardcoded F1 awareness, which it deliberately
# lacks: write_session() serializes whatever SensorConfig list it's given.
# ----------------------------------------------------------------------------------------------------------------------

def sample_session():
    return SessionMetadata(
        session_uid=8723641095837261824,
        session_name="Test Session",
        session_type="race",
        app_version="0.0.1-test",
        game_year=2026,
        formula="F1",
        game_version="1.00",
        timestamp="2024-06-01T14:32:00Z",
        track=TrackInfo(id=999, name="Fake Circuit"),
        laps_count=2,
        session_best=SessionBest(driver_index=1, lap_number=2, lap_time_ms=90000),
    )


def sample_sensors():
    return [
        SensorConfig(key="widget_speed", label="Widget Speed", unit="u/s", type=SensorType.CONTINUOUS),
        SensorConfig(key="gizmo_state", label="Gizmo State", unit="", type=SensorType.DISCRETE),
        SensorConfig(key="gizmo.left.temp", label="Gizmo Left Temp", unit="C", type=SensorType.CONTINUOUS),
    ]


def sample_dtypes():
    """dtype is a write-only, separate-from-SensorConfig mapping -- see writer.py's
    write_session() docstring."""
    return {
        "widget_speed": SensorDtype.FLOAT32,
        "gizmo_state": SensorDtype.INT8,
        "gizmo.left.temp": SensorDtype.FLOAT32,
    }


def sample_drivers():
    return [
        DriverRecord(driver_index=1, name="Test Driver A", team="Nullteam", is_ai=False,
                     car_number=44, nationality="GB", platform="Steam", is_telemetry_public=True),
        DriverRecord(driver_index=2, name="Test Driver B", team="Voidteam", is_ai=False,
                     car_number=7, nationality=None, platform=None, is_telemetry_public=False),
    ]


def _lap(lap_number, lap_time_ms, valid, tyre_compound, tyre_laps, pit_in_lap, pit_out_lap,
         distances, speeds, states, temps, is_good=False):
    return CompletedLap(
        metadata=LapMetadata(
            lap_number=lap_number,
            lap_time_ms=lap_time_ms,
            valid=valid,
            tyre_compound=tyre_compound,
            tyre_laps=tyre_laps,
            pit_in_lap=pit_in_lap,
            pit_out_lap=pit_out_lap,
            num_points=len(distances),
            is_good=is_good,
        ),
        telemetry={
            "lap_distance": distances,
            "widget_speed": speeds,
            "gizmo_state": states,
            "gizmo.left.temp": temps,
        },
    )


def sample_driver_data():
    lap1 = _lap(1, 95000, True, "Medium", 1, False, True,
                [0.0, 100.0, 200.0, 300.0], [100.0, float("nan"), 150.0, 200.0], [1, -1, 2, 3], [20.0, 21.0, 22.0, 23.0])
    lap2 = _lap(2, 90000, True, "Soft", 1, False, False,
                [0.0, 150.0, 300.0], [110.0, 160.0, 210.0], [1, 2, 3], [24.0, 25.0, 26.0])
    in_progress = _lap(3, None, False, "Soft", 2, False, False,
                        [0.0, 50.0], [115.0, 120.0], [1, 1], [24.5, 24.6])
    return {
        1: DriverExportData(driver_index=1, completed_laps=[lap1, lap2], in_progress_lap=in_progress),
    }


def _rebuild_zip(src_path, dst_path, patch_entry=None):
    """Copies every entry from src_path into dst_path, applying patch_entry(name, data) -> data
    to each entry so tests can simulate a hand-edited/forward-compatible .pngt file without
    going through write_session()'s validation."""
    with zipfile.ZipFile(src_path) as src, zipfile.ZipFile(dst_path, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if patch_entry is not None:
                data = patch_entry(item.filename, data)
            dst.writestr(item.filename, data, compress_type=item.compress_type)


def _strip_entry(src_path, dst_path, name_to_remove):
    """Copies every entry from src_path into dst_path except name_to_remove."""
    with zipfile.ZipFile(src_path) as src, zipfile.ZipFile(dst_path, "w") as dst:
        for item in src.infolist():
            if item.filename == name_to_remove:
                continue
            dst.writestr(item.filename, src.read(item.filename), compress_type=item.compress_type)

# ----------------------------------------------------------------------------------------------------------------------
# Round trip
# ----------------------------------------------------------------------------------------------------------------------

def test_round_trip(tmp_path):
    session = sample_session()
    sensors = sample_sensors()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    dest = tmp_path / "session.pngt"

    result = write_session(dest, session, sensors, sample_dtypes(), drivers, driver_data)
    assert result == dest

    parsed = read_session(dest)
    assert parsed.session.session_uid == session.session_uid
    assert parsed.session.session_name == session.session_name
    assert parsed.session.session_type == session.session_type
    assert parsed.session.app_version == session.app_version
    assert parsed.session.game_year == session.game_year
    assert parsed.session.formula == session.formula
    assert parsed.session.game_version == session.game_version
    assert parsed.session.timestamp == session.timestamp
    assert parsed.session.track == session.track
    assert parsed.session.laps_count == session.laps_count
    assert parsed.session.session_best == session.session_best
    assert parsed.sensors == sensors
    assert parsed.drivers == drivers

    laps = read_driver_laps(dest, 1)
    expected_metadata = [
        driver_data[1].completed_laps[0].metadata,
        dataclasses.replace(driver_data[1].completed_laps[1].metadata, is_good=True),  # fastest valid lap, auto-marked
        driver_data[1].in_progress_lap.metadata,
    ]
    assert laps == expected_metadata

    telemetry1 = read_lap_telemetry(dest, 1, 1)
    assert set(telemetry1.keys()) == {"lap_distance", "widget_speed", "gizmo_state", "gizmo.left.temp"}
    assert telemetry1["lap_distance"].dtype == np.float32
    np.testing.assert_allclose(telemetry1["lap_distance"], [0.0, 100.0, 200.0, 300.0])
    assert telemetry1["widget_speed"].dtype == np.float32
    assert np.isnan(telemetry1["widget_speed"][1])
    np.testing.assert_allclose(telemetry1["widget_speed"][[0, 2, 3]], [100.0, 150.0, 200.0])
    assert telemetry1["gizmo_state"].dtype == np.int8
    assert telemetry1["gizmo_state"][1] == -1
    np.testing.assert_array_equal(telemetry1["gizmo_state"][[0, 2, 3]], [1, 2, 3])
    np.testing.assert_allclose(telemetry1["gizmo.left.temp"], [20.0, 21.0, 22.0, 23.0])

    telemetry3 = read_lap_telemetry(dest, 1, 3)
    np.testing.assert_allclose(telemetry3["lap_distance"], [0.0, 50.0])

# ----------------------------------------------------------------------------------------------------------------------
# header.json validation
# ----------------------------------------------------------------------------------------------------------------------

def test_rejects_non_zip_file(tmp_path):
    dest = tmp_path / "bad.pngt"
    dest.write_bytes(b"not a zip file at all")
    with pytest.raises(NotAZipFileError):
        read_header(dest)


def test_rejects_wrong_format(tmp_path):
    dest = tmp_path / "wrong_format.pngt"
    with zipfile.ZipFile(dest, "w") as zf:
        zf.writestr("header.json", json.dumps({"format": "other", "version": 1}))
    with pytest.raises(UnsupportedFormatError):
        read_header(dest)


def test_rejects_wrong_version(tmp_path):
    dest = tmp_path / "wrong_version.pngt"
    with zipfile.ZipFile(dest, "w") as zf:
        zf.writestr("header.json", json.dumps({"format": "pngt", "version": 2}))
    with pytest.raises(UnsupportedVersionError):
        read_header(dest)


def test_rejects_missing_header_keys(tmp_path):
    dest = tmp_path / "no_keys.pngt"
    with zipfile.ZipFile(dest, "w") as zf:
        zf.writestr("header.json", json.dumps({"format": "pngt"}))
    with pytest.raises(InvalidHeaderError):
        read_header(dest)

# ----------------------------------------------------------------------------------------------------------------------
# manifest.json (sensor registry) validation
# ----------------------------------------------------------------------------------------------------------------------

def test_read_manifest_returns_sensor_registry(tmp_path):
    sensors = sample_sensors()
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sensors, sample_dtypes(), sample_drivers(), sample_driver_data())

    read_back = read_manifest(dest)
    assert read_back == sensors


def test_manifest_missing_raises_invalid_manifest_error(tmp_path):
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())

    stripped = tmp_path / "stripped.pngt"
    _strip_entry(dest, stripped, "manifest.json")

    with pytest.raises(InvalidManifestError):
        read_manifest(stripped)
    with pytest.raises(InvalidManifestError):
        read_session(stripped)


def test_manifest_malformed_sensor_entry_raises_invalid_manifest_error(tmp_path):
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())

    def strip_label(name, data):
        if name != "manifest.json":
            return data
        obj = json.loads(data)
        first_key = next(iter(obj["sensors"]))
        del obj["sensors"][first_key]["label"]
        return json.dumps(obj).encode("utf-8")

    patched = tmp_path / "patched.pngt"
    _rebuild_zip(dest, patched, patch_entry=strip_label)

    with pytest.raises(InvalidManifestError):
        read_manifest(patched)


def test_manifest_invalid_sensor_type_raises_invalid_manifest_error(tmp_path):
    # sensor `type` IS validated against a closed set (SensorType), unlike
    # session_type/tyre_compound -- a value outside {continuous, discrete} in
    # manifest.json must fail to read with InvalidManifestError.
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())

    def corrupt_type(name, data):
        if name != "manifest.json":
            return data
        obj = json.loads(data)
        first_key = next(iter(obj["sensors"]))
        obj["sensors"][first_key]["type"] = "not_a_real_type"
        return json.dumps(obj).encode("utf-8")

    patched = tmp_path / "patched.pngt"
    _rebuild_zip(dest, patched, patch_entry=corrupt_type)

    with pytest.raises(InvalidManifestError):
        read_manifest(patched)

# ----------------------------------------------------------------------------------------------------------------------
# Restricted drivers
# ----------------------------------------------------------------------------------------------------------------------

def test_restricted_driver_has_no_folder(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert not any(name.startswith("drivers/02/") for name in names)

    assert read_driver_laps(dest, 2) == []


def test_restricted_driver_in_driver_data_rejected(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    driver_data[2] = DriverExportData(driver_index=2, completed_laps=[], in_progress_lap=None)
    dest = tmp_path / "session.pngt"

    with pytest.raises(ValueError):
        write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

# ----------------------------------------------------------------------------------------------------------------------
# Forward compatibility
# ----------------------------------------------------------------------------------------------------------------------

def test_unknown_sensor_key_tolerated_on_read(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    def patch_lap1_npz(name, data):
        if name != "drivers/01/lap_001.npz":
            return data
        with np.load(BytesIO(data)) as npz:
            arrays = {arr_name: npz[arr_name] for arr_name in npz.files}
        arrays["future_sensor"] = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        buf = BytesIO()
        np.savez(buf, **arrays)
        return buf.getvalue()

    patched = tmp_path / "patched.pngt"
    _rebuild_zip(dest, patched, patch_entry=patch_lap1_npz)

    telemetry = read_lap_telemetry(patched, 1, 1)
    assert "future_sensor" in telemetry
    np.testing.assert_allclose(telemetry["future_sensor"], [1.0, 2.0, 3.0, 4.0])


def test_older_file_fewer_sensors(tmp_path):
    sensors = [SensorConfig(key="widget_speed", label="Widget Speed", unit="u/s", type=SensorType.CONTINUOUS)]
    dtypes = {"widget_speed": SensorDtype.FLOAT32}
    drivers = sample_drivers()
    lap = CompletedLap(
        metadata=LapMetadata(
            lap_number=1, lap_time_ms=95000, valid=True, tyre_compound="Medium", tyre_laps=1,
            pit_in_lap=False, pit_out_lap=True, num_points=2, is_good=False,
        ),
        telemetry={"lap_distance": [0.0, 100.0], "widget_speed": [100.0, 150.0]},
    )
    driver_data = {1: DriverExportData(driver_index=1, completed_laps=[lap], in_progress_lap=None)}
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sensors, dtypes, drivers, driver_data)

    telemetry = read_lap_telemetry(dest, 1, 1)
    assert set(telemetry.keys()) == {"lap_distance", "widget_speed"}


def test_unknown_json_field_tolerated(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    def add_future_field(name, data):
        if name not in ("session.json", "drivers.json", "drivers/01/laps.json"):
            return data
        obj = json.loads(data)
        obj["future_field"] = "surprise"
        return json.dumps(obj).encode("utf-8")

    patched = tmp_path / "patched.pngt"
    _rebuild_zip(dest, patched, patch_entry=add_future_field)

    parsed = read_session(patched)
    assert parsed.session.session_name == session.session_name
    laps = read_driver_laps(patched, 1)
    assert len(laps) == 3

# ----------------------------------------------------------------------------------------------------------------------
# In-progress lap
# ----------------------------------------------------------------------------------------------------------------------

def test_in_progress_lap(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert "drivers/01/lap_003.npz" in names  # 2-digit driver folder, 3-digit lap padding

    laps = read_driver_laps(dest, 1)
    in_progress = next(lap for lap in laps if lap.lap_number == 3)
    assert in_progress.lap_time_ms is None
    assert in_progress.valid is False
    assert in_progress.num_points == 2
    assert in_progress.is_good is False  # default-good logic never applies to in-progress laps

# ----------------------------------------------------------------------------------------------------------------------
# Default-good-lap logic
# ----------------------------------------------------------------------------------------------------------------------

def test_default_good_lap_marks_fastest_valid_lap(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()  # lap1=95000, lap2=90000 (faster), neither marked good by caller
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    laps = {lap.lap_number: lap for lap in read_driver_laps(dest, 1)}
    assert laps[1].is_good is False
    assert laps[2].is_good is True
    assert laps[3].is_good is False  # in-progress, untouched


def test_default_good_lap_respects_caller_marked_lap(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    lap1 = _lap(1, 95000, True, "Medium", 1, False, True,
                [0.0, 100.0], [100.0, 110.0], [1, 1], [20.0, 21.0], is_good=True)  # slower lap, explicitly marked good
    lap2 = _lap(2, 90000, True, "Soft", 1, False, False,
                [0.0, 100.0], [120.0, 130.0], [1, 1], [22.0, 23.0], is_good=False)  # faster lap, not marked
    driver_data = {1: DriverExportData(driver_index=1, completed_laps=[lap1, lap2])}
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    laps = {lap.lap_number: lap for lap in read_driver_laps(dest, 1)}
    assert laps[1].is_good is True   # caller's choice preserved
    assert laps[2].is_good is False  # not auto-promoted since a lap was already marked good

# ----------------------------------------------------------------------------------------------------------------------
# suggest_filename
# ----------------------------------------------------------------------------------------------------------------------

def test_suggest_filename():
    session = sample_session()
    assert suggest_filename(session) == "999-race-2024-06-01-1432.pngt"


def test_write_session_never_overrides_explicit_dest_path(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    dest = tmp_path / "custom_name.pngt"

    result = write_session(dest, session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    assert result == dest
    assert dest.exists()
    assert not (tmp_path / suggest_filename(session)).exists()

# ----------------------------------------------------------------------------------------------------------------------
# write_session validation errors
# ----------------------------------------------------------------------------------------------------------------------

def test_completed_lap_rejects_mismatched_telemetry_lengths():
    # Array-length agreement is CompletedLap's own invariant -- checked at construction,
    # not deferred to write_session().
    good_lap = sample_driver_data()[1].completed_laps[0]
    with pytest.raises(ValueError):
        dataclasses.replace(good_lap, telemetry={**good_lap.telemetry, "widget_speed": [1.0, 2.0]})


def test_write_session_rejects_unregistered_sensor_key(tmp_path):
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    bad_lap = dataclasses.replace(
        driver_data[1].completed_laps[0],
        telemetry={**driver_data[1].completed_laps[0].telemetry, "not_a_real_sensor": [1.0, 2.0, 3.0, 4.0]},
    )
    driver_data[1] = dataclasses.replace(driver_data[1], completed_laps=[bad_lap, driver_data[1].completed_laps[1]])

    with pytest.raises(ValueError):
        write_session(tmp_path / "session.pngt", session, sample_sensors(), sample_dtypes(), drivers, driver_data)


def test_sensor_config_rejects_invalid_type():
    # Sensor `type` IS validated -- unlike session_type/tyre_compound -- and that check is
    # SensorConfig's own invariant, enforced at construction rather than by write_session().
    with pytest.raises(ValueError):
        dataclasses.replace(sample_sensors()[0], type="continuous")  # str, not the enum


def test_write_session_rejects_sensor_missing_from_dtypes(tmp_path):
    # dtype is a separate `dtypes` dict, not a SensorConfig field -- every sensor.key must
    # have an entry or write_session() fails fast rather than raising a confusing KeyError
    # deep in the NPZ writer.
    incomplete_dtypes = {k: v for k, v in sample_dtypes().items() if k != "widget_speed"}
    with pytest.raises(ValueError):
        write_session(tmp_path / "session.pngt", sample_session(), sample_sensors(), incomplete_dtypes,
                       sample_drivers(), sample_driver_data())


def test_write_session_does_not_validate_session_type(tmp_path):
    # session_type is deliberately NOT a closed enum -- see writer.py's _validate_sensors
    # comment. Any string must round-trip untouched.
    session = dataclasses.replace(sample_session(), session_type="not_a_real_session_type")
    dest = write_session(tmp_path / "session.pngt", session, sample_sensors(), sample_dtypes(),
                          sample_drivers(), sample_driver_data())

    assert read_session(dest).session.session_type == "not_a_real_session_type"


def test_write_session_does_not_validate_tyre_compound(tmp_path):
    # tyre_compound is deliberately NOT a closed enum -- the format spec gives it as
    # illustrative examples, not an exhaustive list (unlike session_type/sensor type).
    # Any string must be accepted so this library stays free of sim-specific domain
    # knowledge.
    session = sample_session()
    drivers = sample_drivers()
    driver_data = sample_driver_data()
    odd_metadata = dataclasses.replace(driver_data[1].completed_laps[0].metadata, tyre_compound="Hyperhard")
    odd_lap = dataclasses.replace(driver_data[1].completed_laps[0], metadata=odd_metadata)
    driver_data[1] = dataclasses.replace(driver_data[1], completed_laps=[odd_lap, driver_data[1].completed_laps[1]])

    dest = write_session(tmp_path / "session.pngt", session, sample_sensors(), sample_dtypes(), drivers, driver_data)

    laps = {lap.lap_number: lap for lap in read_driver_laps(dest, 1)}
    assert laps[1].tyre_compound == "Hyperhard"


def test_is_telemetry_public_round_trips_as_bool(tmp_path):
    # is_telemetry_public is a plain bool (not a "Public"/"Restricted" string), so there's
    # no invalid-value question -- just confirm it round-trips correctly for both drivers.
    dest = write_session(tmp_path / "session.pngt", sample_session(), sample_sensors(), sample_dtypes(),
                          sample_drivers(), sample_driver_data())

    parsed = read_session(dest)
    assert parsed.drivers[0].is_telemetry_public is True
    assert parsed.drivers[1].is_telemetry_public is False


def test_driver_export_data_rejects_in_progress_lap_with_lap_time():
    # Whether a lap is "in progress" is DriverExportData's own structure, so the
    # constraint that follows -- no final time, not valid -- is checked at construction.
    data = sample_driver_data()[1]
    bad_metadata = dataclasses.replace(data.in_progress_lap.metadata, lap_time_ms=1000)
    with pytest.raises(ValueError):
        dataclasses.replace(data, in_progress_lap=dataclasses.replace(data.in_progress_lap, metadata=bad_metadata))


def test_driver_export_data_rejects_in_progress_lap_marked_valid():
    data = sample_driver_data()[1]
    bad_metadata = dataclasses.replace(data.in_progress_lap.metadata, valid=True)
    with pytest.raises(ValueError):
        dataclasses.replace(data, in_progress_lap=dataclasses.replace(data.in_progress_lap, metadata=bad_metadata))

# ----------------------------------------------------------------------------------------------------------------------
# delete_laps
# ----------------------------------------------------------------------------------------------------------------------

def _two_driver_dataset():
    drivers = [
        DriverRecord(driver_index=1, name="Test Driver A", team="Nullteam", is_ai=False,
                     car_number=44, nationality="GB", platform="Steam", is_telemetry_public=True),
        DriverRecord(driver_index=2, name="Test Driver C", team="Emptyteam", is_ai=False,
                     car_number=7, nationality=None, platform=None, is_telemetry_public=True),
    ]
    d1_lap1 = _lap(1, 100000, True, "Medium", 1, False, True, [0.0, 100.0], [100.0, 110.0], [1, 1], [20.0, 21.0])
    d1_lap2 = _lap(2, 92000, True, "Soft", 1, False, False, [0.0, 100.0], [120.0, 130.0], [1, 1], [22.0, 23.0])
    d2_lap1 = _lap(1, 91000, True, "Soft", 1, False, True, [0.0, 100.0], [125.0, 135.0], [1, 1], [24.0, 25.0])
    driver_data = {
        1: DriverExportData(driver_index=1, completed_laps=[d1_lap1, d1_lap2]),
        2: DriverExportData(driver_index=2, completed_laps=[d2_lap1]),
    }
    session = dataclasses.replace(
        sample_session(), laps_count=3, session_best=SessionBest(driver_index=2, lap_number=1, lap_time_ms=91000),
    )
    return session, sample_sensors(), sample_dtypes(), drivers, driver_data


def test_delete_laps_removes_specified_lap(tmp_path):
    session, sensors, dtypes, drivers, driver_data = _two_driver_dataset()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sensors, dtypes, drivers, driver_data)

    result = delete_laps(dest, 1, [1])

    assert result.driver_index == 1
    assert result.deleted_lap_numbers == [1]
    assert result.driver_folder_removed is False

    laps = read_driver_laps(dest, 1)
    assert [lap.lap_number for lap in laps] == [2]
    with zipfile.ZipFile(dest) as zf:
        assert "drivers/01/lap_001.npz" not in zf.namelist()
        assert "drivers/01/lap_002.npz" in zf.namelist()


def test_delete_laps_removes_driver_folder_and_recomputes_session_best(tmp_path):
    session, sensors, dtypes, drivers, driver_data = _two_driver_dataset()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sensors, dtypes, drivers, driver_data)

    # driver 2's only lap (91000) is the global best; deleting it should promote driver 1's 92000 lap
    result = delete_laps(dest, 2, [1])

    assert result.driver_folder_removed is True
    assert result.new_session_best == SessionBest(driver_index=1, lap_number=2, lap_time_ms=92000)
    assert result.new_laps_count == 2  # driver 1's remaining 2 laps, driver 2 has none left

    assert read_driver_laps(dest, 2) == []
    with zipfile.ZipFile(dest) as zf:
        assert not any(name.startswith("drivers/02/") for name in zf.namelist())

    parsed = read_session(dest)
    assert parsed.session.laps_count == 2
    assert parsed.session.session_best == SessionBest(driver_index=1, lap_number=2, lap_time_ms=92000)
    # drivers.json entry for driver 2 is unchanged even though their folder is gone
    assert any(d.driver_index == 2 for d in parsed.drivers)


def test_delete_laps_does_not_promote_new_good_lap(tmp_path):
    session, sensors, dtypes, drivers, driver_data = _two_driver_dataset()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sensors, dtypes, drivers, driver_data)

    # driver 1's fastest lap (2, 92000) was auto-marked good by write_session
    assert {lap.lap_number: lap.is_good for lap in read_driver_laps(dest, 1)} == {1: False, 2: True}

    delete_laps(dest, 1, [2])  # delete the good lap

    laps = read_driver_laps(dest, 1)
    assert [lap.lap_number for lap in laps] == [1]
    assert laps[0].is_good is False  # not auto-promoted


def test_delete_laps_raises_for_empty_lap_numbers(tmp_path):
    session, sensors, dtypes, drivers, driver_data = _two_driver_dataset()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sensors, dtypes, drivers, driver_data)

    with pytest.raises(ValueError):
        delete_laps(dest, 1, [])


def test_delete_laps_raises_for_unknown_lap_number(tmp_path):
    session, sensors, dtypes, drivers, driver_data = _two_driver_dataset()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sensors, dtypes, drivers, driver_data)

    with pytest.raises(ValueError):
        delete_laps(dest, 1, [99])


def test_delete_laps_raises_for_unknown_driver(tmp_path):
    session, sensors, dtypes, drivers, driver_data = _two_driver_dataset()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sensors, dtypes, drivers, driver_data)

    with pytest.raises(DriverNotFoundError):
        delete_laps(dest, 55, [1])

# ----------------------------------------------------------------------------------------------------------------------
# mark_lap_good
# ----------------------------------------------------------------------------------------------------------------------

def test_mark_lap_good_marks_previously_not_good_lap(tmp_path):
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())
    assert {lap.lap_number: lap.is_good for lap in read_driver_laps(dest, 1)} == {1: False, 2: True, 3: False}

    result = mark_lap_good(dest, 1, 1)

    assert result == type(result)(driver_index=1, lap_number=1, already_good=False)
    laps = {lap.lap_number: lap.is_good for lap in read_driver_laps(dest, 1)}
    assert laps[1] is True
    assert laps[2] is True  # untouched


def test_mark_lap_good_is_noop_if_already_good(tmp_path):
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())
    before = dest.read_bytes()

    result = mark_lap_good(dest, 1, 2)  # already the auto-marked good lap

    assert result.already_good is True
    assert dest.read_bytes() == before  # file untouched


def test_mark_lap_good_raises_for_unknown_lap(tmp_path):
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())

    with pytest.raises(ValueError):
        mark_lap_good(dest, 1, 99)


def test_mark_lap_good_raises_for_unknown_driver(tmp_path):
    dest = tmp_path / "session.pngt"
    write_session(dest, sample_session(), sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())

    with pytest.raises(DriverNotFoundError):
        mark_lap_good(dest, 55, 1)

# ----------------------------------------------------------------------------------------------------------------------
# rename_session
# ----------------------------------------------------------------------------------------------------------------------

def test_rename_session_updates_name_only(tmp_path):
    session = sample_session()
    dest = tmp_path / "session.pngt"
    write_session(dest, session, sample_sensors(), sample_dtypes(), sample_drivers(), sample_driver_data())

    rename_session(dest, "Renamed Session")

    parsed = read_session(dest)
    assert parsed.session.session_name == "Renamed Session"
    assert parsed.session.session_uid == session.session_uid
    assert parsed.session.track == session.track
    assert parsed.session.laps_count == session.laps_count
    assert parsed.drivers == sample_drivers()
