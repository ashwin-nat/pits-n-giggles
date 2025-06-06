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

import configparser
import os
import sys
import tempfile

from pydantic import ValidationError

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.config import (CaptureSettings, DisplaySettings, ForwardingSettings,
                        LoggingSettings, NetworkSettings, PngSettings,
                        PrivacySettings, StreamOverlay, load_config_from_ini,
                        save_config_to_ini)
from lib.config.config_io import configparser_to_dict, dict_to_configparser

# ----------------------------------------------------------------------------------------------------------------------

class TestF1ConfigBase(F1TelemetryUnitTestsBase):
    pass

class TestNetworkSettings(TestF1ConfigBase):
    """Test NetworkSettings model validation and defaults"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        settings = NetworkSettings()
        self.assertEqual(settings.telemetry_port, 20777)
        self.assertEqual(settings.server_port, 4768)
        self.assertEqual(settings.save_viewer_port, 4769)
        self.assertEqual(settings.udp_tyre_delta_action_code, 11)
        self.assertEqual(settings.udp_custom_action_code, 12)

    def test_valid_port_ranges(self):
        """Test that valid port numbers are accepted"""
        settings = NetworkSettings(
            telemetry_port=1,
            server_port=65535,
            save_viewer_port=8080
        )
        self.assertEqual(settings.telemetry_port, 1)
        self.assertEqual(settings.server_port, 65535)
        self.assertEqual(settings.save_viewer_port, 8080)

    def test_invalid_port_ranges(self):
        """Test that invalid port numbers raise ValidationError"""
        with self.assertRaises(ValidationError):
            NetworkSettings(telemetry_port=-1)

        with self.assertRaises(ValidationError):
            NetworkSettings(server_port=65536)

    def test_action_code_validation(self):
        """Test UDP action code validation"""
        # Valid range
        settings = NetworkSettings(
            udp_tyre_delta_action_code=1,
            udp_custom_action_code=12
        )
        self.assertEqual(settings.udp_tyre_delta_action_code, 1)
        self.assertEqual(settings.udp_custom_action_code, 12)

        # Invalid range
        with self.assertRaises(ValidationError):
            NetworkSettings(udp_tyre_delta_action_code=0)

        with self.assertRaises(ValidationError):
            NetworkSettings(udp_custom_action_code=13)

class TestCaptureSettings(TestF1ConfigBase):
    """Test CaptureSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = CaptureSettings()
        self.assertFalse(settings.post_race_data_autosave)

    def test_boolean_validation(self):
        """Test boolean field validation"""
        settings = CaptureSettings(post_race_data_autosave=True)
        self.assertTrue(settings.post_race_data_autosave)

class TestDisplaySettings(TestF1ConfigBase):
    """Test DisplaySettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = DisplaySettings()
        self.assertEqual(settings.refresh_interval, 200)
        self.assertFalse(settings.disable_browser_autoload)

    def test_refresh_interval_validation(self):
        """Test refresh interval must be positive"""
        settings = DisplaySettings(refresh_interval=100)
        self.assertEqual(settings.refresh_interval, 100)

        with self.assertRaises(ValidationError):
            DisplaySettings(refresh_interval=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(refresh_interval=-1)

class TestLoggingSettings(TestF1ConfigBase):
    """Test LoggingSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = LoggingSettings()
        self.assertEqual(settings.log_file, "png.log")
        self.assertEqual(settings.log_file_size, 1_000_000)

    def test_log_file_size_validation(self):
        """Test log file size must be positive"""
        settings = LoggingSettings(log_file_size=500000)
        self.assertEqual(settings.log_file_size, 500000)

        with self.assertRaises(ValidationError):
            LoggingSettings(log_file_size=0)

        with self.assertRaises(ValidationError):
            LoggingSettings(log_file_size=-1)

class TestPrivacySettings(TestF1ConfigBase):
    """Test PrivacySettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = PrivacySettings()
        self.assertFalse(settings.process_car_setup)

class TestForwardingSettings(TestF1ConfigBase):
    """Test ForwardingSettings model and host:port validation"""

    def test_default_values(self):
        """Test default values"""
        settings = ForwardingSettings()
        self.assertEqual(settings.target_1, "")
        self.assertEqual(settings.target_2, "")
        self.assertEqual(settings.target_3, "")

    def test_valid_hostport_formats(self):
        """Test valid host:port formats"""
        valid_targets = [
            "localhost:8080",
            "127.0.0.1:3000",
            "example.com:80",
            "my-server.domain:65535",
            "192.168.1.1:443"
        ]

        for target in valid_targets:
            settings = ForwardingSettings(target_1=target)
            self.assertEqual(settings.target_1, target)

    def test_empty_targets_allowed(self):
        """Test that empty strings are allowed"""
        settings = ForwardingSettings(
            target_1="",
            target_2=" ",  # Should be stripped to empty
            target_3=None
        )
        self.assertEqual(settings.target_1, "")
        self.assertEqual(settings.target_2, "")
        self.assertEqual(settings.target_3, "")

    def test_invalid_hostport_formats(self):
        """Test invalid host:port formats raise ValidationError"""
        invalid_targets = [
            "localhost",  # No port
            ":8080",      # No host
            "localhost:",  # No port number
            "localhost:abc",  # Non-numeric port
            "localhost:0",    # Port out of range
            "localhost:65536", # Port out of range
            "localhost:8080:extra", # Extra components
            "local host:8080",  # Space in hostname
        ]

        for target in invalid_targets:
            with self.assertRaises(ValidationError):
                ForwardingSettings(target_1=target)

    def test_port_range_validation(self):
        """Test port number range validation"""
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="localhost:0")

        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="localhost:65536")

        # Valid boundaries
        settings1 = ForwardingSettings(target_1="localhost:1")
        settings2 = ForwardingSettings(target_1="localhost:65535")
        self.assertEqual(settings1.target_1, "localhost:1")
        self.assertEqual(settings2.target_1, "localhost:65535")

class TestPngSettings(TestF1ConfigBase):
    """Test the main PngSettings model"""

    def test_complete_model_creation(self):
        """Test creating a complete PngSettings model"""
        settings = PngSettings(
            Network=NetworkSettings(),
            Capture=CaptureSettings(),
            Display=DisplaySettings(),
            Logging=LoggingSettings(),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlay(),
        )

        self.assertIsInstance(settings.Network, NetworkSettings)
        self.assertIsInstance(settings.Capture, CaptureSettings)
        self.assertIsInstance(settings.Display, DisplaySettings)
        self.assertIsInstance(settings.Logging, LoggingSettings)
        self.assertIsInstance(settings.Privacy, PrivacySettings)
        self.assertIsInstance(settings.Forwarding, ForwardingSettings)

    def test_nested_validation(self):
        """Test that nested model validation works"""
        with self.assertRaises(ValidationError):
            PngSettings(
                Network=NetworkSettings(telemetry_port=-1),  # Invalid
                Capture=CaptureSettings(),
                Display=DisplaySettings(),
                Logging=LoggingSettings(),
                Privacy=PrivacySettings(),
                Forwarding=ForwardingSettings()
            )

class TestConfigIO(TestF1ConfigBase):
    """Test configuration I/O functions"""

    def test_configparser_to_dict(self):
        """Test converting ConfigParser to dictionary"""
        cp = configparser.ConfigParser()
        cp['Section1'] = {'key1': 'value1', 'key2': 'value2'}
        cp['Section2'] = {'key3': 'value3'}

        result = configparser_to_dict(cp)
        expected = {
            'Section1': {'key1': 'value1', 'key2': 'value2'},
            'Section2': {'key3': 'value3'}
        }
        self.assertEqual(result, expected)

    def test_dict_to_configparser(self):
        """Test converting dictionary to ConfigParser"""
        data = {
            'Section1': {'key1': 'value1', 'key2': 42},
            'Section2': {'key3': True}
        }

        cp = dict_to_configparser(data)
        self.assertEqual(cp['Section1']['key1'], 'value1')
        self.assertEqual(cp['Section1']['key2'], '42')  # Should be string
        self.assertEqual(cp['Section2']['key3'], 'True')  # Should be string

    def test_save_config_to_ini(self):
        """Test saving configuration to INI file"""
        settings = PngSettings(
            Network=NetworkSettings(telemetry_port=12345),
            Capture=CaptureSettings(post_race_data_autosave=True),
            Display=DisplaySettings(refresh_interval=150),
            Logging=LoggingSettings(log_file="test.log"),
            Privacy=PrivacySettings(process_car_setup=True),
            Forwarding=ForwardingSettings(target_1="localhost:8080"),
            StreamOverlay=StreamOverlay()
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
            StreamOverlay=StreamOverlay(
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
            StreamOverlay=StreamOverlay()
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
