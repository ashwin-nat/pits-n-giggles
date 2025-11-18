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

import os
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin
from ..types.file_path_str import FilePathStr

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class HttpsSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    enabled: bool = Field(
        default=False, description="Enable HTTPS support",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    key_file_path: FilePathStr = Field(
        default="",
        description="Path to SSL private key file",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    cert_file_path: FilePathStr = Field(
        default="",
        description="Path to SSL certificate file",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )

    def model_post_init(self, __context: Any) -> None: # pylint: disable=arguments-differ
        """Validate file existence only if HTTPS is enabled."""
        if self.enabled:
            if not self.key_file_path.strip() or not os.path.isfile(self.key_file_path): # pylint: disable=no-member
                raise ValueError("Key file is required and must exist when HTTPS is enabled")
            if not self.cert_file_path.strip() or not os.path.isfile(self.cert_file_path): # pylint: disable=no-member
                raise ValueError("Certificate file is required and must exist when HTTPS is enabled")

    @property
    def proto(self) -> str:
        return "https" if self.enabled else "http"

    @property
    def cert_path(self) -> Optional[str]:
        """Path to SSL certificate file. Will be None if HTTPS is disabled."""
        return None if not self.enabled else self.cert_file_path

    @property
    def key_path(self) -> Optional[str]:
        """Path to SSL private key file. Will be None if HTTPS is disabled."""
        return None if not self.enabled else self.key_file_path
