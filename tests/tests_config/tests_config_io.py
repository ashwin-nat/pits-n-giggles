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

import os
import sys

from pydantic import ValidationError

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
import sys

from pydantic import ValidationError

from lib.config import LoggingSettings

from .tests_config_base import TestF1ConfigBase
from unittest.mock import Mock, patch

# ----------------------------------------------------------------------------------------------------------------------
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



# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import configparser
import tempfile

from lib.config import (CaptureSettings, DisplaySettings, ForwardingSettings,
                        LoggingSettings, NetworkSettings, PngSettings,
                        PrivacySettings, StreamOverlaySettings,
                        load_config_from_ini, save_config_to_ini)

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestConfigIO(TestF1ConfigBase):
    """Test configuration I/O functions"""

    def test_save_config_to_ini(self):
        """Test saving configuration to INI file"""
        settings = PngSettings(
            Network=NetworkSettings(telemetry_port=12345),
            Capture=CaptureSettings(post_race_data_autosave=True),
            Display=DisplaySettings(refresh_interval=150),
            Logging=LoggingSettings(log_file="test.log"),
            Privacy=PrivacySettings(process_car_setup=True),
            Forwarding=ForwardingSettings(target_1="localhost:8080"),
            StreamOverlay=StreamOverlaySettings()
        )

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            temp_path = f.name

        try:
            save_config_to_ini(settings, temp_path)

            # Verify file was created and contains expected content
            self.assertTrue(os.path.exists(temp_path))

            cp = configparser.ConfigParser()
            cp.read(temp_path)

            self.assertEqual(cp['Network']['telemetry_port'], '12345')
            self.assertEqual(cp['Capture']['post_race_data_autosave'], 'True')
            self.assertEqual(cp['Display']['refresh_interval'], '150')
            self.assertEqual(cp['Logging']['log_file'], 'test.log')
            self.assertEqual(cp['Privacy']['process_car_setup'], 'True')
            self.assertEqual(cp['Forwarding']['target_1'], 'localhost:8080')

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_config_from_existing_ini(self):
        """Test loading configuration from existing INI file"""
        # Create a temporary INI file
        ini_content = """[Network]
telemetry_port = 12345
server_port = 9999

[Capture]
post_race_data_autosave = True

[Display]
refresh_interval = 150

[Logging]
log_file = custom.log

[Privacy]
process_car_setup = True

[Forwarding]
target_1 = localhost:8080
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            f.write(ini_content)
            temp_path = f.name

        try:
            settings = load_config_from_ini(temp_path)

            self.assertEqual(settings.Network.telemetry_port, 12345)
            self.assertEqual(settings.Network.server_port, 9999)
            self.assertTrue(settings.Capture.post_race_data_autosave)
            self.assertEqual(settings.Display.refresh_interval, 150)
            self.assertEqual(settings.Logging.log_file, "custom.log")
            self.assertTrue(settings.Privacy.process_car_setup)
            self.assertEqual(settings.Forwarding.target_1, "localhost:8080")

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_config_from_nonexistent_file(self):
        """Test loading config when file doesn't exist creates default and saves it"""
        # Use tempfile to get a proper temporary directory path
        temp_dir = tempfile.gettempdir()
        nonexistent_path = os.path.join(temp_dir, "nonexistent_config.ini")

        # Ensure file doesn't exist
        if os.path.exists(nonexistent_path):
            os.unlink(nonexistent_path)

        try:
            settings = load_config_from_ini(nonexistent_path)

            # Should return default settings
            self.assertEqual(settings.Network.telemetry_port, 20777)
            self.assertFalse(settings.Capture.post_race_data_autosave)
            self.assertEqual(settings.Display.refresh_interval, 200)

            # File should have been created
            self.assertTrue(os.path.exists(nonexistent_path))

        finally:
            if os.path.exists(nonexistent_path):
                os.unlink(nonexistent_path)

    def test_roundtrip_config_io(self):
        """Test that save/load operations preserve data correctly"""
        original_settings = PngSettings(
            Network=NetworkSettings(
                telemetry_port=11111,
                server_port=22222,
                udp_tyre_delta_action_code=5
            ),
            Capture=CaptureSettings(post_race_data_autosave=True),
            Display=DisplaySettings(
                refresh_interval=300,
                disable_browser_autoload=True
            ),
            Logging=LoggingSettings(
                log_file="roundtrip.log",
                log_file_size=2_000_000
            ),
            Privacy=PrivacySettings(process_car_setup=True),
            Forwarding=ForwardingSettings(
                target_1="server1.example.com:8080",
                target_2="server2.example.com:9090"
            ),
            StreamOverlay=StreamOverlaySettings(
                show_sample_data_at_start=True
            )
        )

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            temp_path = f.name

        try:
            # Save and reload
            save_config_to_ini(original_settings, temp_path)
            loaded_settings = load_config_from_ini(temp_path)

            # Compare all values
            self.assertEqual(loaded_settings.Network.telemetry_port, original_settings.Network.telemetry_port)
            self.assertEqual(loaded_settings.Network.server_port, original_settings.Network.server_port)
            self.assertEqual(loaded_settings.Network.udp_tyre_delta_action_code, original_settings.Network.udp_tyre_delta_action_code)
            self.assertEqual(loaded_settings.Capture.post_race_data_autosave, original_settings.Capture.post_race_data_autosave)
            self.assertEqual(loaded_settings.Display.refresh_interval, original_settings.Display.refresh_interval)
            self.assertEqual(loaded_settings.Display.disable_browser_autoload, original_settings.Display.disable_browser_autoload)
            self.assertEqual(loaded_settings.Logging.log_file, original_settings.Logging.log_file)
            self.assertEqual(loaded_settings.Logging.log_file_size, original_settings.Logging.log_file_size)
            self.assertEqual(loaded_settings.Privacy.process_car_setup, original_settings.Privacy.process_car_setup)
            self.assertEqual(loaded_settings.Forwarding.target_1, original_settings.Forwarding.target_1)
            self.assertEqual(loaded_settings.Forwarding.target_2, original_settings.Forwarding.target_2)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestLoadConfigFromIni(TestF1ConfigBase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ini_path = os.path.join(self.temp_dir.name, "config.ini")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_ini(self, ini_dict: dict[str, dict[str, str]]):
        cp = configparser.ConfigParser()
        cp.read_dict(ini_dict)
        with open(self.ini_path, "w", encoding="utf-8") as f:
            cp.write(f)

    def test_valid_config_loads_correctly(self):
        ini_data = {
            "Network": {"telemetry_port": "20778"},
            "Display": {"refresh_interval": "250"},
            "Logging": {"log_file": "mylog.txt"},
            "Forwarding": {"target_1": "127.0.0.1:9000"},
        }
        self._write_ini(ini_data)

        config = load_config_from_ini(self.ini_path)
        self.assertEqual(config.Network.telemetry_port, 20778)
        self.assertEqual(config.Display.refresh_interval, 250)
        self.assertEqual(config.Logging.log_file, "mylog.txt")
        self.assertEqual(config.Forwarding.target_1, "127.0.0.1:9000")

    def test_invalid_config_creates_backup_and_falls_back_to_defaults(self):
        ini_data = {
            "Display": {"refresh_interval": "0"},  # invalid: must be > 0
            "Logging": {"log_file": "C:/invalid.log"},  # invalid: not relative
        }
        self._write_ini(ini_data)

        config = load_config_from_ini(self.ini_path)
        self.assertEqual(config.Display.refresh_interval, 200)  # default
        self.assertEqual(config.Logging.log_file, "png.log")  # default

        self.assertTrue(os.path.exists(self.ini_path + ".invalid"))

    def test_missing_ini_creates_default_config_file(self):
        self.assertFalse(os.path.exists(self.ini_path))

        config = load_config_from_ini(self.ini_path)
        self.assertTrue(os.path.exists(self.ini_path))
        self.assertIsInstance(config, PngSettings)

    def test_partial_config_with_one_invalid_field_falls_back(self):
        ini_data = {
            "Network": {"telemetry_port": "20779"},
            "Forwarding": {"target_1": "bad-value"},  # invalid format
        }
        self._write_ini(ini_data)

        config = load_config_from_ini(self.ini_path)
        self.assertEqual(config.Network.telemetry_port, 20777)
        self.assertEqual(config.Forwarding.target_1, "")  # fallback default
        self.assertTrue(os.path.exists(self.ini_path + ".invalid"))