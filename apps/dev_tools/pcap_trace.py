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

One record per change of lap number or driver status, for each traced car (the player by default). Each carries the
overall frame, the frame, lap distance, lap time, pit status, and the latest fuel, MGU-K harvest this lap, average
tyre wear and fitted set. A fitted set change, the key events (flashback, session start/end, lights, chequered
flag, retirement), a session UID change (menu packets on UID 0 aside) and the first FINAL_CLASSIFICATION on each
UID come in between. Printed as a table, or with --json as one JSON object per line.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from lib.f1_types import F1PacketBase, F1PacketType, PacketEventData
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

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def trace(file_name: str, cars: List[int], all_events: bool) -> List[Dict[str, Any]]:
    """The timeline records for cars (empty: the player) in file_name. Each has a "kind": "info", "event",
    "session_uid", "final_classification", "tyre_sets" or "lap"."""
    factory = PacketParserFactory(set(F1PacketType), logging.getLogger("pcap_trace"))
    states: Dict[int, CarState] = {car: CarState() for car in cars}
    records: List[Dict[str, Any]] = []
    session_uid: Optional[int] = None
    classified_uids: Set[int] = set()

    for _, raw in F1PacketCapture(file_name=file_name).getPackets():
        packet = factory.parse(raw)
        if packet is None:
            continue
        header = packet.m_header
        if not states:
            player = header.m_playerCarIndex
            states[player] = CarState()
            records.append({"kind": "info", "packet_format": header.m_packetFormat, "player_car": player})
        frames = {"overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier}
        if header.m_sessionUID not in (0, session_uid):
            records.append({"kind": "session_uid", **frames, "from": session_uid, "to": header.m_sessionUID,
                            "packet": header.m_packetId.name})
            session_uid = header.m_sessionUID
        if header.m_packetId == F1PacketType.FINAL_CLASSIFICATION and header.m_sessionUID not in classified_uids:
            classified_uids.add(header.m_sessionUID)
            records.append({"kind": "final_classification", **frames, "session_uid": header.m_sessionUID})
        _apply(packet, states, all_events, records)
    return records


def _apply(packet: F1PacketBase, states: Dict[int, CarState], all_events: bool,
           records: List[Dict[str, Any]]) -> None:
    header = packet.m_header
    frames = {"overall_frame": header.m_overallFrameIdentifier, "frame": header.m_frameIdentifier}
    packet_id = header.m_packetId

    if packet_id == F1PacketType.SESSION and not any(state.lap_key for state in states.values()):
        records.append({"kind": "info", "session_type": str(packet.m_sessionType), "track": str(packet.m_trackId),
                        "track_length": packet.m_trackLength})
    elif packet_id == F1PacketType.EVENT:
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


def as_table_line(record: Dict[str, Any]) -> str:
    """One record as a table line."""
    if record["kind"] == "info":
        return "# " + ", ".join(f"{key} {value}" for key, value in record.items() if key != "kind")
    frames = f"{record['overall_frame']:>7} {record['frame']:>7}"
    if record["kind"] == "event":
        return f"{frames}  EVENT {record['event']} {record['details']}"
    if record["kind"] == "session_uid":
        return f"{frames}  SESSION UID {record['from']} -> {record['to']} on {record['packet']}"
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
    args = parser.parse_args()

    records = trace(args.file_name, args.car, args.all_events)
    if args.json:
        for record in records:
            print(json.dumps(record))
        return
    print("overall   frame")
    for record in records:
        print(as_table_line(record))

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == "__main__":
    main()
