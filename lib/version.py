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

from typing import Dict, Any, Optional, List

import json
import os
import requests
from packaging import version

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------
PNG_RELEASES_API = "https://api.github.com/repos/ashwin-nat/pits-n-giggles/releases"

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_version() -> str:
    """Get the version string from env variable

    Returns:
        str: Version string
    """

    return os.environ.get('PNG_VERSION', 'dev')

def get_releases_info(timeout: float = 5.0, api_endpoint: str = PNG_RELEASES_API) -> Optional[List[Dict[str, Any]]]:
    """Get releases info from GitHub

    Args:
        timeout (float): Timeout for the request in seconds
        api_endpoint (str): GitHub releases API endpoint. Defaults to the official Pits n' Giggles releases API.

    Returns:
        List[Dict[str, Any]]: List of releases
    """
    try:
        response = requests.get(api_endpoint, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        return None

def is_update_available(curr_version_str: str, releases: List[Dict[str, Any]]) -> bool:
    """
    Checks if a newer stable version is available on GitHub.

    Args:
        curr_version_str (str): Current version string.
        releases (List[Dict[str, Any]]): List of releases from GitHub API response.

    Returns:
        bool: True if update is available, False otherwise or on error.

    Caveat:
        This function assumes that the releases are returned in reverse chronological
        order and that the most recent stable (non-prerelease) release is listed first.
        If older versions are published *after* newer ones, this may return incorrect results.
    """
    try:

        curr_version = version.parse(curr_version_str)
        for release in releases:
            if release.get("prerelease", False):
                continue
            if tag := release.get("tag_name", "").lstrip("v"):
                return version.parse(tag) > curr_version

        return False

    except (version.InvalidVersion):
        return False

def get_newer_stable_releases(
    curr_version_str: str,
    releases: List[Dict[str, Any]]
) -> Optional[List[Dict[str, Any]]]:
    """
    Return a list of stable (non-prerelease) releases that are newer than
    the given version.

    Args:
        curr_version_str (str): Current version string.
        releases (List[Dict[str, Any]]): GitHub releases list.

    Returns:
        Optional[List[Dict[str, Any]]]: List of newer stable releases
        or None on error.
    """
    try:
        curr_version = version.parse(curr_version_str)
        newer: List[Dict[str, Any]] = []

        for rel in releases:
            if rel.get("prerelease", False):
                continue

            tag = rel.get("tag_name", "").lstrip("v")
            if not tag:
                continue

            try:
                rel_version = version.parse(tag)
            except version.InvalidVersion:
                continue

            if rel_version > curr_version:
                newer.append(rel)

        return newer

    except version.InvalidVersion:
        return None
