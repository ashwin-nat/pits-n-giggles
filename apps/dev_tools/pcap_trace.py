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

"""Print a car's lap and driver status timeline from an .f1pcap, without running the app.

    poetry run python -m apps.dev_tools.pcap_trace test_data/<file>.f1pcap [--car N ...] [--all-events] [--json]
    poetry run python -m apps.dev_tools.pcap_trace test_data/<file>.f1pcap --around 422.7 [--window 0.1] [--car N ...]

One record per change of lap number or driver status, for each traced car (the player by default). Each carries the
overall frame, the frame, lap distance, lap time, pit status, and the latest fuel, MGU-K harvest this lap, average
tyre wear and fitted set. A fitted set change, the key events (flashback, session start/end, lights, chequered
flag, retirement), a session UID change (menu packets on UID 0 aside), a rewind (the frame goes back while the
overall frame carries on), a restart (both go back to 0) and the first FINAL_CLASSIFICATION on each UID come in
between. Printed as a table, or with --json as one JSON object per line.

--around prints every packet within --window seconds of that session time instead, in capture order, with the
traced cars' values from each packet. A session time seen twice (a flashback) shows both passes.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import json
import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from lib.f1_types import F1PacketBase, F1PacketType, PacketEventData, PacketHeader
from lib.packet_cap import F1PacketCapture
from lib.telemetry_manager.factory import PacketParserFactory

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

KEY_EVENTS = {
    PacketEventData.EventPacketType.FLASHBACK,
    PacketEventData.EventPacketType.SESSION_STARTED,
    PacketEventData.EventPacketType.SESSION_ENDED,
    PacketEventData.EventPacketType.START_LIGHTS,
    PacketEventData.EventPacketType.LIGHTS_OUT,
    PacketEventData.EventPacketType.CHEQUERED_FLAG,
    PacketEventData.EventPacketType.RETIREMENT,
}

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class CarState:
    """The latest values from the packets that aren't printed on their own."""
    fuel: Optional[float] = None
    mguk_mj: Optional[float] = None
    wear: Optional[float] = None
    fitted: Optional[int] = None
    lap_key: Optional[Tuple[int, str]] = None
    position: Optional[Tuple[float, float, float]] = None


@dataclass
class FrameTracker:
    """The last in-order header of the current session, for spotting rewinds and restarts."""
    frame: Optional[int] = None
    overall_frame: Optional[int] = None
    session_time: Optional[float] = None

    def check(self, header: PacketHeader) -> Optional[Dict[str, Any]]:
        """A "rewind" or "restart" record if header's frame went back, else None. A packet that arrives late (both
        frames behind, not a restart) is skipped and doesn't move the tracker."""
        record = None
        if self.frame is not None and header.m_frameIdentifier < self.frame:
            if header.m_overallFrameIdentifier >= self.overall_frame:
                record = self._record("rewind", header)
            elif header.m_frameIdentifier == 0:
                record = self._record("restart", header)
            else:
                return None
        self.frame = header.m_frameIdentifier
        self.overall_frame = header.m_overallFrameIdentifier
        self.session_time = header.m_sessionTime
        return record

    def _record(self, kind: str, header: PacketHeader) -> Dict[str, Any]:
        return {"kind": kind, "overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier,
                "frame_from": self.frame, "time_from": round(self.session_time, 3),
                "time_to": round(header.m_sessionTime, 3), "packet": header.m_packetId.name}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _player_car(header: PacketHeader) -> int:
    """The player's car index from header. Raises ValueError for a recording with no player car (spectating)."""
    if header.m_playerCarIndex == 255:
        raise ValueError("No player car (spectating). Pass --car N")
    return header.m_playerCarIndex


def trace(file_name: str, cars: List[int], all_events: bool, jump_m: Optional[float] = None) -> List[Dict[str, Any]]:
    """The timeline records for cars (empty: the player) in file_name. Each has a "kind": "info", "event",
    "session_uid", "rewind", "restart", "final_classification", "tyre_sets", "lap" or, with jump_m, "jump" (a car's
    MOTION position moved more than jump_m metres since its previous one). Raises ValueError if cars is empty and
    the recording has no player car (spectating)."""
    factory = PacketParserFactory(set(F1PacketType), logging.getLogger("pcap_trace"))
    states: Dict[int, CarState] = {car: CarState() for car in cars}
    records: List[Dict[str, Any]] = []
    session_uid: Optional[int] = None
    frames_seen = FrameTracker()
    classified_uids: Set[int] = set()
    described_uids: Set[int] = set()

    for _, raw in F1PacketCapture(file_name=file_name).getPackets():
        packet = factory.parse(raw)
        if packet is None:
            continue
        header = packet.m_header
        if not states:
            player = _player_car(header)
            states[player] = CarState()
            records.append({"kind": "info", "packet_format": header.m_packetFormat, "player_car": player})
        frames = {"overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier}
        if header.m_sessionUID not in (0, session_uid):
            records.append({"kind": "session_uid", **frames, "from": session_uid, "to": header.m_sessionUID,
                            "packet": header.m_packetId.name})
            session_uid = header.m_sessionUID
            states = {car: CarState() for car in states}
            frames_seen = FrameTracker()
        # Events skipped: a rewind's FLBK burst carries the old session time on the new frame
        if header.m_sessionUID != 0 and header.m_packetId != F1PacketType.EVENT and \
                (frame_record := frames_seen.check(header)):
            records.append(frame_record)
        if header.m_packetId == F1PacketType.FINAL_CLASSIFICATION and header.m_sessionUID not in classified_uids:
            classified_uids.add(header.m_sessionUID)
            records.append({"kind": "final_classification", **frames, "session_uid": header.m_sessionUID})
        if header.m_packetId == F1PacketType.SESSION and header.m_sessionUID not in described_uids | {0}:
            described_uids.add(header.m_sessionUID)
            records.append({"kind": "info", "session_type": str(packet.m_sessionType), "track": str(packet.m_trackId),
                            "track_length": packet.m_trackLength})
        _apply(packet, states, all_events, jump_m, records)
    return records


def _apply(packet: F1PacketBase, states: Dict[int, CarState], all_events: bool, jump_m: Optional[float],
           records: List[Dict[str, Any]]) -> None:
    header = packet.m_header
    frames = {"overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier}
    packet_id = header.m_packetId

    if packet_id == F1PacketType.EVENT:
        if all_events or packet.m_eventCode in KEY_EVENTS:
            details = str(packet.mEventDetails) if packet.mEventDetails is not None else ""
            records.append({"kind": "event", **frames, "event": packet.m_eventCode.name, "details": details})

    for car, state in states.items():
        if packet_id == F1PacketType.CAR_STATUS:
            status = packet.m_carStatusData[car]
            state.fuel = round(status.m_fuelInTank, 3)
            state.mguk_mj = round(status.m_ersHarvestedThisLapMGUK / 1e6, 3)
        elif packet_id == F1PacketType.CAR_DAMAGE:
            state.wear = round(sum(packet.m_carDamageData[car].m_tyresWear) / 4, 3)
        elif packet_id == F1PacketType.MOTION and jump_m is not None:
            motion = packet.m_carMotionData[car]
            position = (motion.m_worldPositionX, motion.m_worldPositionY, motion.m_worldPositionZ)
            if state.position is not None and (moved := math.dist(state.position, position)) > jump_m:
                records.append({"kind": "jump", **frames, "car": car, "session_time": round(header.m_sessionTime, 3),
                                "moved_m": round(moved, 1), "from": [round(v, 1) for v in state.position],
                                "to": [round(v, 1) for v in position]})
            state.position = position
        elif packet_id == F1PacketType.TYRE_SETS and packet.m_carIdx == car:
            if packet.m_fittedIdx != state.fitted:
                records.append({"kind": "tyre_sets", **frames, "car": car, "fitted_from": state.fitted,
                                "fitted_to": packet.m_fittedIdx})
            state.fitted = packet.m_fittedIdx
        elif packet_id == F1PacketType.LAP_DATA:
            lap = packet.m_lapData[car]
            key = (lap.m_currentLapNum, str(lap.m_driverStatus))
            if key != state.lap_key:
                records.append({"kind": "lap", **frames, "car": car, "lap": lap.m_currentLapNum,
                                "status": str(lap.m_driverStatus), "distance": round(lap.m_lapDistance, 1),
                                "lap_time_ms": lap.m_currentLapTimeInMS, "pit": str(lap.m_pitStatus),
                                "fuel": state.fuel, "mguk_mj": state.mguk_mj, "wear": state.wear,
                                "fitted": state.fitted})
                state.lap_key = key


def find_lap_time(file_name: str, cars: List[int], lap: int, lap_time_ms: int) -> List[Dict[str, Any]]:
    """A "lap_time" record for each time one of cars (empty: the player) reached lap_time_ms on lap, with the
    session time, frames and lap distance of that LAP_DATA. A flashback past that point gives a second record.
    Raises ValueError as trace() does."""
    factory = PacketParserFactory({F1PacketType.LAP_DATA}, logging.getLogger("pcap_trace"))
    records: List[Dict[str, Any]] = []
    last: Dict[int, Tuple[int, int]] = {}      # car -> (lap, lap time) of its previous LAP_DATA
    armed: Dict[int, bool] = {}                # car -> this pass started at or before lap_time_ms
    for _, raw in F1PacketCapture(file_name=file_name).getPackets():
        packet = factory.parse(raw)
        if packet is None:
            continue
        header = packet.m_header
        if not cars:
            cars = [_player_car(header)]
        for car in cars:
            lap_data = packet.m_lapData[car]
            now = (lap_data.m_currentLapNum, lap_data.m_currentLapTimeInMS)
            # A pass starts on entering the lap or on a rewind (lap time going back)
            if now[0] == lap and (car not in last or last[car][0] != lap or now[1] < last[car][1]):
                armed[car] = now[1] <= lap_time_ms
            if now[0] == lap and armed.get(car) and now[1] >= lap_time_ms:
                armed[car] = False
                records.append({"kind": "lap_time", "car": car, "lap": lap, "lap_time_ms": lap_time_ms,
                                "session_time": round(header.m_sessionTime, 3),
                                "overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier,
                                "distance": round(lap_data.m_lapDistance, 1)})
            last[car] = now
    return records


def packets_around(file_name: str, cars: List[int], times: List[float], window: float) -> List[Dict[str, Any]]:
    """A "packet" record for every packet within window seconds of any of the session times, in capture order.
    Each carries the capture index, session time, frames, packet type and, under "cars", the values that packet
    holds for each of cars (empty: the player). Raises ValueError as trace() does."""
    factory = PacketParserFactory(set(F1PacketType), logging.getLogger("pcap_trace"))
    records: List[Dict[str, Any]] = []
    for index, (_, raw) in enumerate(F1PacketCapture(file_name=file_name).getPackets()):
        packet = factory.parse(raw)
        if packet is None:
            continue
        header = packet.m_header
        if not cars:
            cars = [_player_car(header)]
        if all(abs(header.m_sessionTime - time) > window for time in times):
            continue
        values = {car: car_values for car in cars if (car_values := _car_values(packet, car))}
        record = {"kind": "packet", "index": index, "session_time": round(header.m_sessionTime, 3),
                  "overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier,
                  "packet": header.m_packetId.name, "cars": values}
        if header.m_packetId == F1PacketType.EVENT:
            record["event"] = packet.m_eventCode.name
        records.append(record)
    return records


def _car_values(packet: F1PacketBase, car: int) -> Dict[str, Any]:
    """The values packet holds for car, for the packet types a debugging session usually needs."""
    packet_id = packet.m_header.m_packetId
    if packet_id == F1PacketType.LAP_DATA:
        lap = packet.m_lapData[car]
        return {"lap": lap.m_currentLapNum, "distance": round(lap.m_lapDistance, 1),
                "lap_time_ms": lap.m_currentLapTimeInMS, "status": str(lap.m_driverStatus)}
    if packet_id == F1PacketType.MOTION:
        motion = packet.m_carMotionData[car]
        return {"x": round(motion.m_worldPositionX, 2), "y": round(motion.m_worldPositionY, 2),
                "z": round(motion.m_worldPositionZ, 2), "yaw": round(motion.m_yaw, 3)}
    if packet_id == F1PacketType.CAR_TELEMETRY:
        telemetry = packet.m_carTelemetryData[car]
        return {"speed": telemetry.m_speed, "gear": telemetry.m_gear, "throttle": round(telemetry.m_throttle, 2),
                "brake": round(telemetry.m_brake, 2)}
    if packet_id == F1PacketType.CAR_STATUS:
        status = packet.m_carStatusData[car]
        return {"fuel": round(status.m_fuelInTank, 3), "ers_store_mj": round(status.m_ersStoreEnergy / 1e6, 3)}
    if packet_id == F1PacketType.CAR_DAMAGE:
        return {"wear": round(sum(packet.m_carDamageData[car].m_tyresWear) / 4, 3)}
    if packet_id == F1PacketType.TYRE_SETS and packet.m_carIdx == car:
        return {"fitted": packet.m_fittedIdx}
    return {}


def as_table_line(record: Dict[str, Any]) -> str:
    """One record as a table line."""
    if record["kind"] == "info":
        return "# " + ", ".join(f"{key} {value}" for key, value in record.items() if key != "kind")
    if record["kind"] == "lap_time":
        return (f"# car {record['car']} reached {record['lap_time_ms']} ms on lap {record['lap']} at session time "
                f"{record['session_time']}, overall {record['overall_frame']}, frame {record['frame']}, "
                f"d={record['distance']}")
    if record["kind"] == "packet":
        values = "  ".join(f"car {car}: " + " ".join(f"{key}={value}" for key, value in car_values.items())
                           for car, car_values in record["cars"].items())
        event = record.get("event", "")
        return (f"{record['index']:>8} {record['session_time']:>9.3f} {record['overall_frame']:>7} "
                f"{record['frame']:>7}  {record['packet']:<20} {event}{values}")
    frames = f"{record['overall_frame']:>7} {record['frame']:>7}"
    if record["kind"] == "event":
        return f"{frames}  EVENT {record['event']} {record['details']}"
    if record["kind"] == "session_uid":
        return f"{frames}  SESSION UID {record['from']} -> {record['to']} on {record['packet']}"
    if record["kind"] in {"rewind", "restart"}:
        return (f"{frames}  {record['kind'].upper()} frame {record['frame_from']} -> {record['frame']}, "
                f"session time {record['time_from']} -> {record['time_to']} on {record['packet']}")
    if record["kind"] == "jump":
        return (f"{frames}  car {record['car']:>2} JUMP {record['moved_m']} m at session time "
                f"{record['session_time']}: {record['from']} -> {record['to']}")
    if record["kind"] == "final_classification":
        return f"{frames}  FINAL_CLASSIFICATION on UID {record['session_uid']}"
    if record["kind"] == "tyre_sets":
        return f"{frames}  car {record['car']:>2} TYRE_SETS fitted {record['fitted_from']} -> {record['fitted_to']}"
    return (f"{frames}  car {record['car']:>2} lap {record['lap']:>2} {record['status']:<11} "
            f"d={record['distance']:9.1f} t={record['lap_time_ms']:>6} pit={record['pit']:<11} "
            f"fuel={record['fuel']} mguk={record['mguk_mj']}MJ wear={record['wear']} fitted={record['fitted']}")


def main() -> None:
    """Parse args and print the trace."""
    parser = argparse.ArgumentParser(description="Print a car's lap and driver status timeline from an .f1pcap")
    parser.add_argument("file_name", help="The .f1pcap file")
    parser.add_argument("--car", type=int, action="append", default=[],
                        help="Car index to trace, repeatable. Defaults to the player")
    parser.add_argument("--all-events", action="store_true", help="Print every event, not just the key ones")
    parser.add_argument("--json", action="store_true", help="One JSON object per line instead of a table")
    parser.add_argument("--around", type=float, metavar="SESSION_TIME",
                        help="Print every packet near this session time instead of the timeline")
    parser.add_argument("--window", type=float, default=0.1, metavar="SECONDS",
                        help="With --around or --at-lap: how far either side of it to print (default 0.1)")
    parser.add_argument("--jumps", type=float, metavar="METRES",
                        help="Add a timeline line wherever a car's position moves more than this between packets")
    parser.add_argument("--at-lap", type=int, metavar="LAP",
                        help="With --lap-time: print every packet around each time the car reached it on this lap")
    parser.add_argument("--lap-time", type=float, metavar="SECONDS", help="With --at-lap: the lap time, e.g. 68.260")
    args = parser.parse_args()

    if (args.at_lap is None) != (args.lap_time is None):
        parser.error("--at-lap and --lap-time go together")
    packet_mode = args.around is not None or args.at_lap is not None
    if args.around is not None and args.at_lap is not None:
        parser.error("--around and --at-lap are alternatives")
    if packet_mode and args.jumps is not None:
        parser.error("--jumps adds to the timeline, not to --around or --at-lap")

    try:
        if args.at_lap is not None:
            records = find_lap_time(args.file_name, args.car, args.at_lap, round(args.lap_time * 1000))
            records += packets_around(args.file_name, args.car, [r["session_time"] for r in records], args.window)
        elif args.around is not None:
            records = packets_around(args.file_name, args.car, [args.around], args.window)
        else:
            records = trace(args.file_name, args.car, args.all_events, args.jumps)
    except ValueError as error:
        parser.error(str(error))
    if args.json:
        for record in records:
            print(json.dumps(record))
        return
    if packet_mode:
        print("   index  sess_time overall   frame  packet")
    else:
        print("overall   frame")
    for record in records:
        print(as_table_line(record))

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == "__main__":
    main()
