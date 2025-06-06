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

class TestEdgeCases(TestF1ConfigBase):
    """Test edge cases and error conditions"""

    def test_malformed_ini_file(self):
        """Test handling of malformed INI files"""
        malformed_content = """[Network
telemetry_port = not_a_number
[Capture]
invalid_key = value
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            f.write(malformed_content)
            temp_path = f.name

        try:
            # Should handle malformed INI gracefully or raise appropriate error
            with self.assertRaises((ValidationError, configparser.Error)):
                load_config_from_ini(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_malformed_ini_section_header(self):
        """Test handling of syntactically malformed INI section headers"""
        malformed_section_content = """
[Network
telemetry_port = 12345
server_port = 9999

[Capture
capture_enabled = true
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            f.write(malformed_section_content)
            temp_path = f.name

        try:
            # Should raise configparser.Error due to malformed section headers
            with self.assertRaises(configparser.Error):
                load_config_from_ini(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled"""
        # Leading whitespace should cause validation error due to regex pattern
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="  localhost:8080")

        # Test with only trailing whitespace - should be stripped by rstrip()
        settings = ForwardingSettings(target_1="localhost:8080   ")
        self.assertEqual(settings.target_1, "localhost:8080")

        # Test with no whitespace
        settings2 = ForwardingSettings(target_1="localhost:8080")
        self.assertEqual(settings2.target_1, "localhost:8080")

        # Test empty string with whitespace gets stripped to empty (allowed)
        settings3 = ForwardingSettings(target_1="   ")
        self.assertEqual(settings3.target_1, "")

class TestSampleSettingsFixture(TestF1ConfigBase):
    """Test class that uses a sample settings setup"""

    def setUp(self):
        """Set up sample settings for testing"""
        self.sample_settings = PngSettings(
            Network=NetworkSettings(),
            Capture=CaptureSettings(),
            Display=DisplaySettings(),
            Logging=LoggingSettings(),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlaySettings()
        )

    def test_sample_settings_created(self):
        """Test that sample settings are properly created"""
        self.assertIsNotNone(self.sample_settings)
        self.assertIsInstance(self.sample_settings, PngSettings)
        self.assertEqual(self.sample_settings.Network.telemetry_port, 20777)

class TestMissingSectionsAndKeys(TestF1ConfigBase):

    def setUp(self):
        """Set up temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_ini_file(self, content: str) -> str:
        """Helper to create a temporary INI file with given content"""
        file_path = os.path.join(self.temp_dir, "test_config.ini")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def test_missing_entire_sections(self):
        """Test when entire sections are missing from INI file"""
        ini_content = """
[Network]
telemetry_port = 30777
server_port = 5000

[Capture]
post_race_data_autosave = true
"""
        file_path = self._create_ini_file(ini_content)

        config = load_config_from_ini(file_path)

        # Verify existing sections have correct values
        self.assertEqual(config.Network.telemetry_port, 30777)
        self.assertEqual(config.Network.server_port, 5000)
        self.assertTrue(config.Capture.post_race_data_autosave)

        # Verify missing sections have default values
        self.assertEqual(config.Display.refresh_interval, 200)  # Default
        self.assertFalse(config.Display.disable_browser_autoload)  # Default
        self.assertEqual(config.Logging.log_file, "png.log")  # Default
        self.assertEqual(config.Logging.log_file_size, 1_000_000)  # Default
        self.assertFalse(config.Privacy.process_car_setup)  # Default
        self.assertEqual(config.Forwarding.target_1, "")  # Default
        self.assertEqual(config.Forwarding.target_2, "")  # Default
        self.assertEqual(config.Forwarding.target_3, "")  # Default
        self.assertFalse(config.StreamOverlay.show_sample_data_at_start)  # Default

    def test_missing_keys_in_existing_sections(self):
        """Test when sections exist but some keys are missing"""
        ini_content = """
[Network]
telemetry_port = 25000

[Display]
refresh_interval = 500

[Logging]
log_file = custom.log

[Privacy]

[Forwarding]
target_1 = localhost:8080

[StreamOverlay]
"""
        file_path = self._create_ini_file(ini_content)

        config = load_config_from_ini(file_path)

        # Verify existing keys have correct values
        self.assertEqual(config.Network.telemetry_port, 25000)
        self.assertEqual(config.Display.refresh_interval, 500)
        self.assertEqual(config.Logging.log_file, "custom.log")
        self.assertEqual(config.Forwarding.target_1, "localhost:8080")

        # Verify missing keys have default values
        self.assertEqual(config.Network.server_port, 4768)  # Default
        self.assertEqual(config.Network.save_viewer_port, 4769)  # Default
        self.assertEqual(config.Network.udp_tyre_delta_action_code, 11)  # Default
        self.assertEqual(config.Network.udp_custom_action_code, 12)  # Default
        self.assertFalse(config.Display.disable_browser_autoload)  # Default
        self.assertEqual(config.Logging.log_file_size, 1_000_000)  # Default
        self.assertFalse(config.Privacy.process_car_setup)  # Default
        self.assertEqual(config.Forwarding.target_2, "")  # Default
        self.assertEqual(config.Forwarding.target_3, "")  # Default
        self.assertFalse(config.StreamOverlay.show_sample_data_at_start)  # Default

    def test_partial_network_section(self):
        """Test Network section with only some keys present"""
        ini_content = """
[Network]
telemetry_port = 21000
udp_custom_action_code = 5
"""
        file_path = self._create_ini_file(ini_content)

        config = load_config_from_ini(file_path)

        # Verify present keys
        self.assertEqual(config.Network.telemetry_port, 21000)
        self.assertEqual(config.Network.udp_custom_action_code, 5)

        # Verify missing keys have defaults
        self.assertEqual(config.Network.server_port, 4768)
        self.assertEqual(config.Network.save_viewer_port, 4769)
        self.assertEqual(config.Network.udp_tyre_delta_action_code, 11)

    def test_empty_sections(self):
        """Test when sections exist but are completely empty"""
        ini_content = """
[Network]

[Capture]

[Display]

[Logging]

[Privacy]

[Forwarding]

[StreamOverlay]
"""
        file_path = self._create_ini_file(ini_content)

        config = load_config_from_ini(file_path)

        # All values should be defaults
        self.assertEqual(config.Network.telemetry_port, 20777)
        self.assertEqual(config.Network.server_port, 4768)
        self.assertEqual(config.Network.save_viewer_port, 4769)
        self.assertEqual(config.Network.udp_tyre_delta_action_code, 11)
        self.assertEqual(config.Network.udp_custom_action_code, 12)

        self.assertFalse(config.Capture.post_race_data_autosave)

        self.assertEqual(config.Display.refresh_interval, 200)
        self.assertFalse(config.Display.disable_browser_autoload)

        self.assertEqual(config.Logging.log_file, "png.log")
        self.assertEqual(config.Logging.log_file_size, 1_000_000)

        self.assertFalse(config.Privacy.process_car_setup)

        self.assertEqual(config.Forwarding.target_1, "")
        self.assertEqual(config.Forwarding.target_2, "")
        self.assertEqual(config.Forwarding.target_3, "")

        self.assertFalse(config.StreamOverlay.show_sample_data_at_start)

    def test_mixed_missing_sections_and_keys(self):
        """Test complex scenario with mix of missing sections and keys"""
        ini_content = """
[Network]
telemetry_port = 19999
server_port = 6000

[Display]
disable_browser_autoload = true

[Privacy]
process_car_setup = true

[Forwarding]
target_2 = example.com:9090
"""
        file_path = self._create_ini_file(ini_content)

        config = load_config_from_ini(file_path)

        # Verify present values
        self.assertEqual(config.Network.telemetry_port, 19999)
        self.assertEqual(config.Network.server_port, 6000)
        self.assertTrue(config.Display.disable_browser_autoload)
        self.assertTrue(config.Privacy.process_car_setup)
        self.assertEqual(config.Forwarding.target_2, "example.com:9090")

        # Verify missing keys in present sections have defaults
        self.assertEqual(config.Network.save_viewer_port, 4769)
        self.assertEqual(config.Network.udp_tyre_delta_action_code, 11)
        self.assertEqual(config.Network.udp_custom_action_code, 12)
        self.assertEqual(config.Display.refresh_interval, 200)
        self.assertEqual(config.Forwarding.target_1, "")
        self.assertEqual(config.Forwarding.target_3, "")

        # Verify completely missing sections have all defaults
        self.assertFalse(config.Capture.post_race_data_autosave)
        self.assertEqual(config.Logging.log_file, "png.log")
        self.assertEqual(config.Logging.log_file_size, 1_000_000)
        self.assertFalse(config.StreamOverlay.show_sample_data_at_start)

    def test_only_one_section_present(self):
        """Test when only a single section is present in INI file"""
        ini_content = """
[Logging]
log_file = special.log
log_file_size = 500000
"""
        file_path = self._create_ini_file(ini_content)

        config = load_config_from_ini(file_path)

        # Verify the present section
        self.assertEqual(config.Logging.log_file, "special.log")
        self.assertEqual(config.Logging.log_file_size, 500000)

        # Verify all other sections have defaults
        self.assertEqual(config.Network.telemetry_port, 20777)
        self.assertEqual(config.Network.server_port, 4768)
        self.assertFalse(config.Capture.post_race_data_autosave)
        self.assertEqual(config.Display.refresh_interval, 200)
        self.assertFalse(config.Privacy.process_car_setup)
        self.assertEqual(config.Forwarding.target_1, "")
        self.assertFalse(config.StreamOverlay.show_sample_data_at_start)

    def test_config_saved_when_missing_sections_or_keys(self):
        """Test that config is saved when missing sections/keys are added"""
        ini_content = """
[Network]
telemetry_port = 20777

[Forwarding]
target_1 = localhost:8080
"""

        file_path = self._create_ini_file(ini_content)

        # Load and modify config (this should fill missing sections/keys with defaults)
        config = load_config_from_ini(file_path)

        # Re-save the config back to file
        save_config_to_ini(config, file_path)

        # Reload it and verify all values are present
        with open(file_path, encoding='utf-8') as f:
            saved_content = f.read()

        # Check that values which were missing are now present in the file
        self.assertIn("[Display]", saved_content)
        self.assertIn("refresh_interval = 200", saved_content)
        self.assertIn("disable_browser_autoload = False", saved_content)

        self.assertIn("[Logging]", saved_content)
        self.assertIn("log_file = png.log", saved_content)

        self.assertIn("[Privacy]", saved_content)
        self.assertIn("process_car_setup = False", saved_content)

        self.assertIn("[StreamOverlay]", saved_content)
        self.assertIn("show_sample_data_at_start = False", saved_content)

        # Ensure original values are still present
        self.assertIn("telemetry_port = 20777", saved_content)
        self.assertIn("target_1 = localhost:8080", saved_content)
