---
description: Scaffold a new F1 packet type across lib/f1_types and lib/telemetry_manager
allowed-tools: Read, Glob, Grep, Edit, Write, Bash(grep:*)
---

Scaffold a new F1 packet type following the exact patterns used by existing packets.

## Input

The user must provide:
- **Packet ID** (integer, e.g. `16`)
- **Packet name** (e.g. `PacketCarMotionExData`)
- **Fields** — a list of field names, types, and struct format characters (or a description to derive them from)

If any of these are missing, ask before proceeding.

## Steps

1. **Read a reference packet** to understand the exact pattern to follow:
   - Read `lib/f1_types/packet_2_lap_data.py` (a typical multi-record packet)
   - Read `lib/f1_types/base_pkt.py` to understand `F1PacketBase`, `F1SubPacketBase`
   - Read `lib/f1_types/__init__.py` to see the export list

2. **Create `lib/f1_types/packet_<ID>_<snake_name>.py`**:
   - Follow the MIT license header present in all existing packets
   - Define any sub-record class as `<Name>` extending `F1SubPacketBase` with:
     - `PACKET_FORMAT` (struct format string)
     - `PACKET_LEN = struct.calcsize(PACKET_FORMAT)`
     - `__init__(self, data: bytes)` that unpacks and assigns all fields
     - `__str__` and `toJSON()` methods matching the style of existing packets
   - Define the top-level `Packet<Name>` extending `F1PacketBase` with `from_bytes(cls, header, data)` classmethod
   - Add the `F1PacketType.<ENUM_NAME>` member in `lib/f1_types/header.py`, and set
     `PACKET_ID = F1PacketType.<ENUM_NAME>` on the class. That registers it as the parser for that type;
     `PacketParserFactory` looks it up from there, so the factory needs no edit

3. **Register in `lib/f1_types/__init__.py`**:
   - Import the new class
   - Add it to `__all__` following the alphabetical/numeric order of existing exports

4. **Add the new type to the expected map** in `tests/f1_types/tests_base.py::test_parsers_match_the_packet_classes`

5. **Summarise** what was created and which files were modified, including the struct format used and packet size in bytes.
