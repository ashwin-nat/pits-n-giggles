# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

from .base import HighFreqBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class Vec3f(HighFreqBase):
    x: float
    y: float
    z: float

    @classmethod
    def from_json(cls, json_data):
        return cls(
            x = json_data["x"],
            y = json_data["y"],
            z = json_data["z"],
        )

@dataclass
class Orientation(HighFreqBase):
    yaw: float
    pitch: float
    roll: float

    @classmethod
    def from_json(cls, json_data):
        return cls(
            yaw = json_data["yaw"],
            pitch = json_data["pitch"],
            roll = json_data["roll"],
        )

@dataclass
class GForce(HighFreqBase):
    lateral: float
    longitudinal: float
    vertical: float

    @classmethod
    def from_json(cls, json_data):
        return cls(
            lateral = json_data["lateral"],
            longitudinal = json_data["longitudinal"],
            vertical = json_data["vertical"],
        )

@dataclass
class CarMotion(HighFreqBase):
    world_position: Vec3f
    world_velocity: Vec3f
    world_forward_dir: Vec3f
    world_right_dir: Vec3f
    g_force: GForce
    orientation: Orientation

    @classmethod
    def from_json(cls, json_data):
        return cls(
            world_position = Vec3f.from_json(json_data["world-position"]),
            world_velocity = Vec3f.from_json(json_data["world-velocity"]),
            world_forward_dir = Vec3f.from_json(json_data["world-forward-dir"]),
            world_right_dir = Vec3f.from_json(json_data["world-right-dir"]),
            g_force = GForce.from_json(json_data["g-force"]),
            orientation = Orientation.from_json(json_data["orientation"])
        )

@dataclass
class DriverMotionInfo(HighFreqBase):
    name: str
    team: str
    track_position: float
    index: int
    is_ref: bool
    car_motion: CarMotion

    @classmethod
    def from_json(cls, json_data, ref_index: int):
        return cls(
            name = json_data["name"],
            team = json_data["team"],
            track_position = json_data["track-position"],
            index = json_data["index"],
            is_ref = (json_data["index"] == ref_index),
            car_motion = CarMotion.from_json(json_data["motion"]),
        )

@dataclass
class LiveSessionMotionInfo(HighFreqBase):
    motion_data: list[DriverMotionInfo]

    @classmethod
    def from_json(cls, json_data):

        motion_data = json_data["motion"]
        ref_index   = json_data["ref-index"]
        return cls(
            motion_data = [
                DriverMotionInfo.from_json(motion_data_per_driver, ref_index)
                for motion_data_per_driver in motion_data
            ]
        )
