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

from typing import Any, ClassVar, Dict

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class SaveViewerSettings(ConfigDiffMixin, BaseModel):

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    enable_write_api: bool = Field(
        default=True,
        description="Allow Write Operations",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info" : [
                    "Allows session rename, marking laps as good, and lap deletion "
                    "through the web viewer. Enabled by default for normal local use. "
                    "If you're hosting the save viewer server for others to access over "
                    "the internet — league admins sharing session data with drivers, "
                    "content creators streaming or publishing their viewer, or anyone "
                    "else exposing this to people outside their own machine — consider "
                    "disabling this. This app has no authentication or access control "
                    "by design, so anyone with network access to a publicly hosted "
                    "server could otherwise rename, mark, or delete your sessions."
                ],
            }
        }
    )
