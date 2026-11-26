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

import ipaddress
import re
from typing import Any, ClassVar, Dict, Optional, Tuple

from pydantic import BaseModel, Field, field_validator, model_validator

from .diff import ConfigDiffMixin
from .utils import ConflictError

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_LOCALHOST_ALIASES = {"localhost", "127.0.0.1", "::1"}

# One part of a hostname between dots: 1-63 letters, digits or hyphens, not starting or ending with a hyphen.
# Allows "my-pc", "lan", "1a"; catches "-pc", "pc-", "" (as in "a..b") and "my_pc"
_HOSTNAME_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")
# Only digits and dots, like "192.168.1.10" or "999.999.999.999": can only be meant as an IPv4 address
_DOTTED_NUMERIC = re.compile(r"[0-9.]+")

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _is_valid_host(host: str) -> bool:
    """Whether host can be a forwarding target: an IPv4 address or a hostname (RFC 1123). Checks the spelling
    only; the name is not looked up, so a valid hostname may still not resolve.

    Accepted: "192.168.1.10", "127.0.0.1", "localhost", "MyPC", "my-pc.lan", "1a.example"

    Rejected:
        "999.999.999.999", "1.2.3", "010.0.0.1"  digits and dots, but not a valid IPv4 address
        "-pc", "pc-.lan", "a..b", ".lan", "lan."  a part starts or ends with "-", or is empty
        "my_pc", "my pc"                          a character other than a letter, digit, "-" or "."
        "a.123"                                   last part all digits; no real domain ends like that
        "::1", "[::1]"                            IPv6; the forwarder only sends over IPv4
        a part over 63 characters, or a whole name over 253
    """
    # The forwarder's socket is AF_INET, so IPv6 is not accepted
    if _DOTTED_NUMERIC.fullmatch(host):
        try:
            ipaddress.IPv4Address(host)
        except ValueError:
            return False
        return True
    labels = host.split(".")
    return len(host) <= 253 and all(_HOSTNAME_LABEL.fullmatch(label) for label in labels) and \
        not labels[-1].isdigit()

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class ForwardingSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    target_1: Optional[str] = Field(
        default="",
        description="Target 1 (host:port)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    target_2: Optional[str] = Field(
        default="",
        description="Target 2 (host:port)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    target_3: Optional[str] = Field(
        default="",
        description="Target 3 (host:port)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )

    hostport_pattern: ClassVar[re.Pattern] = re.compile(
        r"""
        ^                             # Start of string
        ([a-zA-Z0-9.-]+)              # Hostname or IP
        :
        ([0-9]{1,5})                  # Port number
        $                             # End of string
        """,
        re.VERBOSE,
    )

    # Pydantic v2 field validators receive the model class as 'cls' automatically.
    # Not a classmethod, so we disable the no-self-argument warning.
    @field_validator('target_1', 'target_2', 'target_3', mode='before')
    def validate_hostport(cls, val): # pylint: disable=no-self-argument
        if val is None:
            return ""
        if not isinstance(val, str):
            raise ValueError(f"Invalid host:port format: '{val}'")
        v = val.strip()
        if not v:
            return v  # allow empty string
        match = cls.hostport_pattern.match(v)
        if not match:
            raise ValueError(f"Invalid host:port format: '{v}'")
        if not _is_valid_host(match.group(1)):
            raise ValueError(f"Invalid host in '{v}': expected an IPv4 address or a hostname")
        port = int(match.group(2))
        if port < 1 or port > 65535:
            raise ValueError(f"Port number out of range in '{v}'")
        return v

    def _parse_hostport(self, value: str) -> tuple[str, int]:
        """
        Parse a host:port string into (host, port) tuple.

        Raises:
            ValueError: if format is invalid or port is out of range.
        """
        host, port_str = value.strip().split(":")
        return host, int(port_str)

    @staticmethod
    def _parse_target(value: str) -> tuple[str, int]:
        host, port = value.split(":", 1)
        return host, int(port)

    @property
    def target_1_tuple(self) -> Optional[Tuple[str, int] | None]:
        return self._parse_target(self.target_1) if self.target_1 else None

    @property
    def target_2_tuple(self) -> Optional[Tuple[str, int] | None]:
        return self._parse_target(self.target_2) if self.target_2 else None

    @property
    def target_3_tuple(self) -> Optional[Tuple[str, int] | None]:
        return self._parse_target(self.target_3) if self.target_3 else None

    @property
    def forwarding_targets(self) -> list[tuple[str, int]]:
        return [
            t for t in (
                self.target_1_tuple,
                self.target_2_tuple,
                self.target_3_tuple,
            )
            if t is not None
        ]

    @staticmethod
    def _normalize_host(host: str) -> str:
        """
        Normalize hostnames so localhost variants are treated the same.
        """
        if host in _LOCALHOST_ALIASES:
            return "localhost"
        return host.lower()

    @model_validator(mode="after")
    def _validate_no_duplicate_targets(self):
        seen: dict[tuple[str, int], str] = {}  # (normalized host, port) -> field name

        for field_name in ("target_1", "target_2", "target_3"):
            target = getattr(self, f"{field_name}_tuple")
            if target is None:
                continue

            host, port = target

            key = (self._normalize_host(host), port)
            if key in seen:
                raise ConflictError(f"Duplicate forwarding target detected: {host}:{port}", [seen[key], field_name])

            seen[key] = field_name

        return self
