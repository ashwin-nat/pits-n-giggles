import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import sys
import os
import configparser
import subprocess
import threading
import time
from typing import Dict, Optional

class SubApp:
    """Class to manage a sub-application process"""
    def __init__(self, name: str, app_path: str, console_app):
        self.name = name
        self.app_path = app_path
        self.console_app = console_app
        self.process: Optional[subprocess.Popen] = None
        self.status_var = tk.StringVar(value="Stopped")
        self.monitor_thread = None
        self.is_running = False

    def start(self):
        """Start the sub-application"""
        if self.is_running:
            self.console_app.log(f"{self.name} is already running.")
            return

        try:
            # For demonstration, we're stubbing the actual app launch
            # In a real app, you'd use something like:
            # self.process = subprocess.Popen([sys.executable, self.app_path],
            #                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Stub implementation to simulate app launch
            self.console_app.log(f"Starting {self.name}...")
            self.process = True  # Just a stub, would be a real process object
            self.is_running = True
            self.status_var.set("Running")

            # Start a monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()

            self.console_app.log(f"{self.name} started successfully.")
        except Exception as e:
            self.console_app.log(f"Error starting {self.name}: {e}")
            self.status_var.set("Error")

    def stop(self):
        """Stop the sub-application"""
        if not self.is_running:
            self.console_app.log(f"{self.name} is not running.")
            return

        try:
            self.console_app.log(f"Stopping {self.name}...")

            # In a real app, you'd use:
            # if self.process:
            #     self.process.terminate()
            #     self.process.wait(timeout=5)

            # Stub implementation
            time.sleep(0.5)  # Simulate some shutdown time
            self.process = None
            self.is_running = False
            self.status_var.set("Stopped")
            self.console_app.log(f"{self.name} stopped successfully.")
        except Exception as e:
            self.console_app.log(f"Error stopping {self.name}: {e}")
            self.status_var.set("Error")

    def _monitor(self):
        """Monitor the sub-application and update its status"""
        # In a real app, this would check if the process is still alive
        # and capture output from stdout/stderr
        while self.is_running:
            # For demonstration, we'll occasionally log something
            time.sleep(5)
            if self.is_running:  # Check again in case it was stopped while sleeping
                self.console_app.log(f"{self.name} - Heartbeat check")

            # In a real app, you might do:
            # if self.process and self.process.poll() is not None:
            #     self.is_running = False
            #     self.status_var.set("Crashed")
            #     self.console_app.log(f"{self.name} has terminated unexpectedly")
            #     break
            #
            # Read output from the process
            # if self.process:
            #     stdout_data = self.process.stdout.readline().decode().strip()
            #     if stdout_data:
            #         self.console_app.log(f"{self.name}: {stdout_data}")


class SettingsWindow:
    def __init__(self, parent, app, config_file="app_settings.ini"):
        self.parent = parent  # This should be a Tkinter widget
        self.app = app  # Reference to the ConsoleApp instance
        self.config_file = config_file
        self.settings = configparser.ConfigParser()

        # Default settings
        self.default_settings = {
            "Network": {
                "telemetry_port": "20777",
                "server_port": "5000",
                "udp_custom_action_code": "12",
                "udp_tyre_delta_action_code": "11"
            },
            "Capture": {
                "packet_capture_mode": "disabled",
                "post_race_data_autosave": "True"
            },
            "Display": {
                "refresh_interval": "200",
                "disable_browser_autoload": "False"
            },
            "Logging": {
                "log_file": "png.log",
                "log_file_size": "1000000"
            },
            "Privacy": {
                "process_car_setup": "False"
            },
            "Forwarding": {
                "target1": "",
                "target2": "",
                "target3": "",
                "target_moza": "localhost:22024",
                "target_sec_mon": "localhost:22025"
            },
            "Stream Overlay": {
                "show_sample_data_at_start": "true"
            },
            "SubApps": {
                "subapp1_path": "subapp1.py",
                "subapp2_path": "subapp2.py"
            }
        }

        # Load or create settings
        self.load_settings()

        # Create settings window
        self.window = tk.Toplevel(parent)
        self.window.title("Application Settings")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs for each section
        self.create_tabs()

        # Create save/cancel buttons
        self.create_buttons()

    def load_settings(self):
        """Load settings from file or create with defaults"""
        if os.path.exists(self.config_file):
            self.settings.read(self.config_file)

        # Ensure all sections and keys exist
        for section, options in self.default_settings.items():
            if not self.settings.has_section(section):
                self.settings.add_section(section)

            for key, value in options.items():
                if not self.settings.has_option(section, key):
                    self.settings.set(section, key, value)

    def save_settings(self):
        """Save settings to file"""
        with open(self.config_file, 'w') as f:
            self.settings.write(f)

        self.app.log(f"Settings saved to {self.config_file}")

    def create_tabs(self):
        """Create tabs for each settings section"""
        self.entry_vars = {}

        for section in self.settings.sections():
            tab = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(tab, text=section)

            # Create a frame for this section with a scrollbar
            canvas = tk.Canvas(tab)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Add settings fields
            for i, (key, value) in enumerate(self.settings[section].items()):
                # Create a label and entry for each setting
                label = ttk.Label(scrollable_frame, text=key.replace('_', ' ').title() + ":")
                label.grid(row=i, column=0, sticky="w", padx=5, pady=5)

                # Use different controls based on value type
                if value.lower() in ['true', 'false']:
                    # Boolean - use checkbox
                    var = tk.BooleanVar(value=value.lower() == 'true')
                    control = ttk.Checkbutton(scrollable_frame, variable=var)
                elif key == 'packet_capture_mode':
                    # Enumeration - use combobox
                    var = tk.StringVar(value=value)
                    control = ttk.Combobox(scrollable_frame, textvariable=var,
                                          values=["disabled", "enabled", "auto"])
                    control.set(value)
                else:
                    # Text entry for everything else
                    var = tk.StringVar(value=value)
                    control = ttk.Entry(scrollable_frame, textvariable=var, width=30)

                control.grid(row=i, column=1, sticky="ew", padx=5, pady=5)

                # Store the variable for later retrieval
                if section not in self.entry_vars:
                    self.entry_vars[section] = {}
                self.entry_vars[section][key] = var

    def create_buttons(self):
        """Create save and cancel buttons"""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        save_button = ttk.Button(button_frame, text="Save", command=self.on_save)
        save_button.pack(side=tk.RIGHT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def on_save(self):
        """Save settings from UI to config"""
        try:
            for section, options in self.entry_vars.items():
                for key, var in options.items():
                    # Convert boolean to string
                    value = str(var.get()) if isinstance(var, tk.BooleanVar) else var.get()
                    self.settings.set(section, key, value)

            self.save_settings()
            self.window.destroy()

            # Notify the app to reload sub-app paths
            self.app.load_subapp_paths()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")


class ConsoleApp:
    def __init__(self, root):
        self.root = root
        self.version = "1.0.0"
        self.app_name = "Console Logger"
        self.config_file = "app_settings.ini"

        # Initialize sub-apps dict
        self.subapps: Dict[str, SubApp] = {}

        # Configure the main window
        root.title(f"{self.app_name} v{self.version}")
        root.geometry("900x700")  # Larger default size for subapp controls

        # Create main frames
        self.header_frame = ttk.Frame(root, padding="10")
        self.header_frame.pack(fill=tk.X)

        self.subapps_frame = ttk.LabelFrame(root, text="Sub-Applications", padding="10")
        self.subapps_frame.pack(fill=tk.X, padx=10, pady=5)

        self.console_frame = ttk.Frame(root, padding="10")
        self.console_frame.pack(fill=tk.BOTH, expand=True)

        # Set up the header section
        self.setup_header()

        # Set up the console section
        self.setup_console()

        # Load settings and configure sub-apps
        self.load_settings()
        self.setup_subapps()

        # Redirect stdout to our console
        self.stdout_original = sys.stdout
        sys.stdout = self

        # Initial log message
        self.log("Application started")

    def load_settings(self):
        """Load application settings"""
        self.settings = configparser.ConfigParser()

        # Create default settings if config file doesn't exist
        if not os.path.exists(self.config_file):
            default_settings = {
                "Network": {
                    "telemetry_port": "20777",
                    "server_port": "5000",
                    "udp_custom_action_code": "12",
                    "udp_tyre_delta_action_code": "11"
                },
                "Capture": {
                    "packet_capture_mode": "disabled",
                    "post_race_data_autosave": "True"
                },
                "Display": {
                    "refresh_interval": "200",
                    "disable_browser_autoload": "False"
                },
                "Logging": {
                    "log_file": "png.log",
                    "log_file_size": "1000000"
                },
                "Privacy": {
                    "process_car_setup": "False"
                },
                "Forwarding": {
                    "target1": "",
                    "target2": "",
                    "target3": "",
                    "target_moza": "localhost:22024",
                    "target_sec_mon": "localhost:22025"
                },
                "Stream Overlay": {
                    "show_sample_data_at_start": "true"
                },
                "SubApps": {
                    "subapp1_path": "subapp1.py",
                    "subapp2_path": "subapp2.py"
                }
            }

            for section, options in default_settings.items():
                self.settings.add_section(section)
                for key, value in options.items():
                    self.settings.set(section, key, value)

            with open(self.config_file, 'w') as f:
                self.settings.write(f)

        else:
            self.settings.read(self.config_file)

    def load_subapp_paths(self):
        """Load/reload sub-app paths from settings"""
        # First, stop any running sub-apps
        for subapp in self.subapps.values():
            if subapp.is_running:
                subapp.stop()

        # Clear existing UI
        for widget in self.subapps_frame.winfo_children():
            widget.destroy()

        # Clear existing subapps
        self.subapps.clear()

        # Load settings
        self.load_settings()

        # Setup subapps with new paths
        self.setup_subapps()

    def setup_subapps(self):
        """Set up the sub-apps UI and control"""
        # Get subapp paths from settings
        if not self.settings.has_section("SubApps"):
            self.settings.add_section("SubApps")
            self.settings.set("SubApps", "subapp1_path", "subapp1.py")
            self.settings.set("SubApps", "subapp2_path", "subapp2.py")
            with open(self.config_file, 'w') as f:
                self.settings.write(f)

        # Create subapp instances
        self.subapps["SubApp1"] = SubApp("SubApp1", self.settings.get("SubApps", "subapp1_path"), self)
        self.subapps["SubApp2"] = SubApp("SubApp2", self.settings.get("SubApps", "subapp2_path"), self)

        # Create UI for each subapp
        for i, (name, subapp) in enumerate(self.subapps.items()):
            frame = ttk.Frame(self.subapps_frame)
            frame.grid(row=0, column=i, padx=10, pady=5)

            # Add controls for this subapp
            label = ttk.Label(frame, text=f"{name}:")
            label.grid(row=0, column=0, padx=5, pady=5)

            status_label = ttk.Label(frame, textvariable=subapp.status_var, width=10)
            status_label.grid(row=0, column=1, padx=5, pady=5)

            # Configure status label colors based on status
            def update_status_color(status_var, label):
                status = status_var.get()
                if status == "Running":
                    label.configure(foreground="green")
                elif status == "Stopped":
                    label.configure(foreground="black")
                else:  # Error or other states
                    label.configure(foreground="red")

            # Initial color update
            update_status_color(subapp.status_var, status_label)

            # Set up a trace on the status variable to update colors
            subapp.status_var.trace_add("write", lambda *args, sv=subapp.status_var, lbl=status_label:
                                        update_status_color(sv, lbl))

            start_button = ttk.Button(frame, text="Start", command=lambda s=subapp: s.start())
            start_button.grid(row=0, column=2, padx=5, pady=5)

            stop_button = ttk.Button(frame, text="Stop", command=lambda s=subapp: s.stop())
            stop_button.grid(row=0, column=3, padx=5, pady=5)

    def setup_header(self):
        # App info section
        info_frame = ttk.Frame(self.header_frame)
        info_frame.pack(side=tk.LEFT)

        app_label = ttk.Label(info_frame, text=f"{self.app_name}", font=("Arial", 14, "bold"))
        app_label.pack(side=tk.LEFT)

        version_label = ttk.Label(info_frame, text=f"v{self.version}", font=("Arial", 10))
        version_label.pack(side=tk.LEFT, padx=(5, 0))

        # Buttons section
        buttons_frame = ttk.Frame(self.header_frame)
        buttons_frame.pack(side=tk.RIGHT)

        self.settings_button = ttk.Button(buttons_frame, text="Settings", command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_button = ttk.Button(buttons_frame, text="Clear Log", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(buttons_frame, text="Save Log", command=self.save_log)
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))

        self.test_button = ttk.Button(buttons_frame, text="Test Log", command=self.test_log)
        self.test_button.pack(side=tk.LEFT)

    def setup_console(self):
        # Create a text widget for the console
        self.console = tk.Text(self.console_frame, wrap=tk.WORD, bg="#000000", fg="#FFFFFF",
                              font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.console, orient=tk.VERTICAL, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)

        # Make text read-only
        self.console.configure(state=tk.DISABLED)

    def log(self, message):
        """Add a message to the console with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, formatted_message)
        self.console.see(tk.END)  # Auto-scroll to the end
        self.console.configure(state=tk.DISABLED)

    def clear_log(self):
        """Clear the console log"""
        self.console.configure(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.configure(state=tk.DISABLED)
        self.log("Log cleared")

    def save_log(self):
        """Save the console log to a file"""
        try:
            filename = f"console_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(self.console.get(1.0, tk.END))
            self.log(f"Log saved to {filename}")
        except Exception as e:
            self.log(f"Error saving log: {e}")

    def test_log(self):
        """Add some test log entries"""
        self.log("This is a test log entry")
        self.log("Another test log entry")
        print("This is printed using print()")
        print("Multiple\nline\nprint\nstatement")

    def open_settings(self):
        """Open the settings window"""
        self.log("Opening settings window")
        # Pass the root window as the parent and the app instance as a reference
        settings_window = SettingsWindow(self.root, self, self.config_file)

    def write(self, text):
        """Handle print statements by redirecting to our log"""
        if text.strip():  # Only process non-empty strings
            self.log(text.rstrip())

    def flush(self):
        """Required for stdout redirection"""
        pass

    def on_closing(self):
        """Stop all running sub-apps and restore stdout before closing"""
        for name, subapp in self.subapps.items():
            if subapp.is_running:
                self.log(f"Stopping {name}...")
                subapp.stop()

        sys.stdout = self.stdout_original
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")  # Use a modern theme

    app = ConsoleApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()