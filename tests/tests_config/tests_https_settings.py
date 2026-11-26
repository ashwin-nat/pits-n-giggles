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
# pylint: skip-file

"""HttpsSettings rules the field spec table does not cover: defaults, the key/cert file checks when enabled, the
proto/key_path/cert_path values, and paths kept while HTTPS is toggled. Each field's type is in
tests_config_properties.py."""

import allure
import pytest
from pydantic import ValidationError

from lib.config import HttpsSettings

pytestmark = allure.feature("HTTPS settings")


@pytest.fixture
def key_and_cert(tmp_path):
    """Paths of an existing key file and an existing cert file."""
    key, cert = tmp_path / "server.key", tmp_path / "server.crt"
    key.touch()
    cert.touch()
    return str(key), str(cert)

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

@allure.story("Defaults")
@allure.title("Default HttpsSettings serve plain HTTP with no key or cert")
def test_default_values():
    """
    Builds HttpsSettings with no arguments.

    Expected: HTTPS is off, both paths are None, proto is "http", and key_path/cert_path are None.
    """
    settings = HttpsSettings()

    assert settings.enabled is False
    assert (settings.key_file_path, settings.cert_file_path) == (None, None)
    assert settings.proto == "http"
    assert (settings.key_path, settings.cert_path) == (None, None)

# -------------------------------------- FILE CHECKS WHEN ENABLED ------------------------------------------------------

@allure.story("File checks when enabled")
@allure.title("Enabling HTTPS without a key file is rejected")
def test_enabled_without_key_rejected():
    """
    Enables HTTPS with a cert path but no key path.

    Expected: a ValidationError saying the key file is required.
    """
    with pytest.raises(ValidationError, match="Key file is required"):
        HttpsSettings(enabled=True, cert_file_path="some/cert.pem")


@allure.story("File checks when enabled")
@allure.title("Enabling HTTPS with a key file but no cert file is rejected")
def test_enabled_without_cert_rejected(key_and_cert):
    """
    Enables HTTPS with an existing key file and no cert path.

    Expected: a ValidationError saying the certificate file is required.
    """
    key, _ = key_and_cert
    with pytest.raises(ValidationError, match="Certificate file is required"):
        HttpsSettings(enabled=True, key_file_path=key)


@allure.story("File checks when enabled")
@allure.title("Enabling HTTPS with key and cert paths that do not exist is rejected")
def test_enabled_with_missing_files_rejected():
    """
    Enables HTTPS with key and cert paths that point at no file.

    Expected: a ValidationError saying the key file is required (the key is checked first).
    """
    with pytest.raises(ValidationError, match="Key file is required"):
        HttpsSettings(enabled=True, key_file_path="/non/existent/key.pem", cert_file_path="/non/existent/cert.pem")


@allure.story("File checks when enabled")
@allure.title("Enabling HTTPS with existing key and cert files serves HTTPS")
def test_enabled_with_files_accepted(key_and_cert):
    """
    Enables HTTPS with an existing key file and an existing cert file.

    Expected: the model builds, keeps both paths, and proto is "https".
    """
    key, cert = key_and_cert
    settings = HttpsSettings(enabled=True, key_file_path=key, cert_file_path=cert)

    assert (settings.key_file_path, settings.cert_file_path) == (key, cert)
    assert settings.proto == "https"

# -------------------------------------- DERIVED VALUES ----------------------------------------------------------------

@allure.story("Derived values")
@allure.title("key_path and cert_path give the files only while HTTPS is enabled")
def test_key_and_cert_path_follow_enabled(key_and_cert):
    """
    Enables HTTPS with existing files, reads key_path/cert_path, then turns HTTPS off and reads them again.

    Expected: the file paths while enabled, None once disabled.
    """
    key, cert = key_and_cert
    settings = HttpsSettings(enabled=True, key_file_path=key, cert_file_path=cert)
    assert (settings.key_path, settings.cert_path) == (key, cert)

    settings.enabled = False
    assert (settings.key_path, settings.cert_path) == (None, None)
    assert (settings.key_file_path, settings.cert_file_path) == (key, cert)

# -------------------------------------- TOGGLING ----------------------------------------------------------------------

@allure.story("Toggling")
@allure.title("Turning HTTPS off keeps the key and cert paths through a save and reload ({files})")
@pytest.mark.parametrize("files", ["existing", "missing"])
def test_disabled_keeps_paths_through_reload(key_and_cert, files):
    """
    Builds HttpsSettings with HTTPS off and key/cert paths set (existing files, or paths to no file as a repair
    leaves them), then dumps it and validates the dump, as a save and reload would.

    Expected: both builds succeed, HTTPS stays off, and both paths are kept unchanged.
    """
    key, cert = key_and_cert if files == "existing" else ("/non/existent/key.pem", "/non/existent/cert.pem")
    settings = HttpsSettings(enabled=False, key_file_path=key, cert_file_path=cert)

    reloaded = HttpsSettings.model_validate(settings.model_dump())

    assert reloaded.proto == "http"
    assert (reloaded.key_file_path, reloaded.cert_file_path) == (key, cert)


@allure.story("Toggling")
@allure.title("Turning HTTPS back on after a reload serves HTTPS with the kept files")
def test_reenabled_after_reload_uses_kept_files(key_and_cert):
    """
    Saves HttpsSettings with HTTPS off and existing key/cert files, reloads the dump with enabled set to True.

    Expected: the model builds, proto is "https", and key_path/cert_path are the original files.
    """
    key, cert = key_and_cert
    saved = HttpsSettings(enabled=False, key_file_path=key, cert_file_path=cert).model_dump()

    settings = HttpsSettings.model_validate({**saved, "enabled": True})

    assert settings.proto == "https"
    assert (settings.key_path, settings.cert_path) == (key, cert)
