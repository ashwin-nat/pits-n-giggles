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

from typing import Any, ClassVar, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model

from .diff import ConfigDiffMixin

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

# Single source of truth for pit time loss, for every circuit and every game.
#   track name -> { game key -> default seconds lost (or None if unknown) }
# Adding a new circuit: add one row. Contributing data for a game (new or existing):
# add/fill in that game's key in the relevant rows. Nothing outside this dict changes.
# Track names/order must stay stable since they are also the JSON keys in saved configs.
PIT_TIME_LOSS_DEFAULTS: Dict[str, Dict[str, Optional[float]]] = {
    "Melbourne":            {"f1": 18.0, "f2": None},
    "Shanghai":             {"f1": 22.0, "f2": None},
    "Suzuka":               {"f1": 22.0, "f2": None},
    "Sakhir":               {"f1": 23.0, "f2": None},
    "Jeddah":               {"f1": 18.0, "f2": None},
    "Miami":                {"f1": 19.0, "f2": None},
    "Imola":                {"f1": 27.0, "f2": None},
    "Monaco":               {"f1": 19.0, "f2": None},
    "Catalunya":            {"f1": 21.0, "f2": None},
    "Montreal":             {"f1": 16.0, "f2": None},
    "Austria":              {"f1": 19.0, "f2": None},
    "Austria_Reverse":      {"f1": 19.0, "f2": None},
    "Silverstone":          {"f1": 28.0, "f2": None},
    "Silverstone_Reverse":  {"f1": None, "f2": None},
    "Hungaroring":          {"f1": 20.0, "f2": None},
    "Zandvoort":            {"f1": 18.0, "f2": None},
    "Spa":                  {"f1": 18.0, "f2": None},
    "Zandvoort_Reverse":    {"f1": 18.0, "f2": None},
    "Monza":                {"f1": 24.0, "f2": None},
    "Baku":                 {"f1": 18.0, "f2": None},
    "Singapore":            {"f1": 26.0, "f2": None},
    "Texas":                {"f1": 20.0, "f2": None},
    "Mexico":               {"f1": 22.0, "f2": None},
    "Brazil":               {"f1": 20.0, "f2": None},
    "Las_Vegas":            {"f1": 20.0, "f2": None},
    "Losail":               {"f1": 25.0, "f2": None},
    "Abu_Dhabi":            {"f1": 19.0, "f2": None},
    "Paul_Ricard":          {"f1": None, "f2": None},
    "Portimao":             {"f1": None, "f2": None},
    "Madrid":               {"f1": None, "f2": None},
}

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class _PitTimeLossBase(ConfigDiffMixin, BaseModel):
    """Common base for per-game pit time loss models. Not adding field level metadata
    since whole section is hidden in UI."""

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible": True,
    }

def make_pit_time_loss_model(model_name: str, game_key: str) -> Type[BaseModel]:
    """Build a pit time loss config model for one game from PIT_TIME_LOSS_DEFAULTS.

    Every circuit in PIT_TIME_LOSS_DEFAULTS becomes a field, sourced from that game's
    key (explicitly None where unknown). Field names/order are identical across games
    and stable release-to-release, since they are the JSON keys persisted in saved configs.
    """
    fields = {
        track: (Optional[float], Field(per_game[game_key]))
        for track, per_game in PIT_TIME_LOSS_DEFAULTS.items()
    }
    return create_model(model_name, __base__=_PitTimeLossBase, **fields)

PitTimeLossF1 = make_pit_time_loss_model("PitTimeLossF1", "f1")

# No known per-track pit time loss data for F2 yet, so every track defaults to None.
# When real values are available, add an "f2" entry to the relevant rows in
# PIT_TIME_LOSS_DEFAULTS above — nothing else needs to change.
PitTimeLossF2 = make_pit_time_loss_model("PitTimeLossF2", "f2")
