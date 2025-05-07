import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import sys
import os
import configparser
import itertools
import subprocess
import threading
import time
from typing import Dict, Optional


# Define racing theme colors
COLOR_THEME = {
    "background": "#1E1E1E",       # Dark background
    "foreground": "#E0E0E0",       # Light text
    "accent1": "#FF2800",          # Racing red
    "accent2": "#303030",          # Dark gray
    "console_bg": "#000000",       # Console black
    "console_fg": "#00FF00",       # Terminal green
    "running": "#00CC00",          # Green for running status
    "stopped": "#FF2800",          # Red for stopped status
    "warning": "#FFA500"           # Orange for warnings
}


class SubApp:
    """Class to manage a sub-application process"""
    def __init__(self, name: str, app_path: str, display_name: str, start_by_default: bool, console_app: "RacingConsoleApp"):
        self.name = name
        self.app_path = app_path
        self.display_name = display_name
        self.console_app = console_app
        self.process: Optional[subprocess.Popen] = None
        self.status_var = tk.StringVar(value="Stopped")
        self.monitor_thread = None
        self.is_running = False

    def start(self):
        """Start the sub-application"""
        if self.is_running:
            self.console_app.log(f"{self.display_name} is already running.")
            return

        try:
            # In a real app, you'd use:
            # self.process = subprocess.Popen([sys.executable, self.app_path],
            #                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # For demonstration, we're simulating app launch
            self.console_app.log(f"Starting {self.display_name}...")
            self.process = True  # Just a stub for demonstration
            self.is_running = True
            self.status_var.set("Running")

            # Start a monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()

            self.console_app.log(f"{self.display_name} started successfully.")
        except Exception as e:
            self.console_app.log(f"Error starting {self.display_name}: {e}")
            self.status_var.set("Error")

    def stop(self):
        """Stop the sub-application"""
        if not self.is_running:
            self.console_app.log(f"{self.display_name} is not running.")
            return

        try:
            self.console_app.log(f"Stopping {self.display_name}...")

            # In a real app, you'd use:
            # if self.process:
            #     self.process.terminate()
            #     self.process.wait(timeout=5)

            # Simulation
            time.sleep(0.5)  # Simulate shutdown time
            self.process = None
            self.is_running = False
            self.status_var.set("Stopped")
            self.console_app.log(f"{self.display_name} stopped successfully.")
        except Exception as e:
            self.console_app.log(f"Error stopping {self.display_name}: {e}")
            self.status_var.set("Error")

    def _monitor(self):
        """Monitor the sub-application and update its status"""
        while self.is_running:
            # For demonstration, we'll occasionally log something
            time.sleep(5)
            if self.is_running:  # Check again in case it was stopped while sleeping
                self.console_app.log(f"{self.display_name} - Heartbeat check")


class SettingsWindow:
    def __init__(self, parent, app, config_file="app_settings.ini"):
        self.parent = parent
        self.app = app
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
                "log_file": "racing_console.log",
                "log_file_size": "1000000"
            },
            "Privacy": {
                "process_car_setup": "False"
            },
            "Forwarding": {
                "target_moza": "localhost:22024",
                "target_sec_mon": "localhost:22025"
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

        # Apply theme
        self.window.configure(bg=COLOR_THEME["background"])

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
            canvas = tk.Canvas(tab, bg=COLOR_THEME["background"])
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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")


class RacingConsoleApp:
    def __init__(self, root):
        self.root = root
        self.version = "1.0.0"
        self.app_name = "Racing Console"
        self.config_file = "racing_console_settings.ini"

        # Apply theme to root window
        self.root.configure(bg=COLOR_THEME["background"])

        # Initialize sub-apps dict
        self.subapps: Dict[str, SubApp] = {}

        # Configure the main window
        root.title(f"{self.app_name} v{self.version}")
        root.geometry("900x700")

        # Create custom style
        self.create_custom_style()

        # Create main frames
        self.header_frame = ttk.Frame(root, padding="10", style="Racing.TFrame")
        self.header_frame.pack(fill=tk.X)

        self.subapps_frame = ttk.LabelFrame(root, text="Race Components", padding="10", style="Racing.TLabelframe")
        self.subapps_frame.pack(fill=tk.X, padx=10, pady=5)

        self.console_frame = ttk.Frame(root, padding="10", style="Racing.TFrame")
        self.console_frame.pack(fill=tk.BOTH, expand=True)

        # Set up the header section
        self.setup_header()

        # Set up the console section
        self.setup_console()

        # Configure hardcoded sub-apps
        self.setup_subapps()

        # Load settings
        self.load_settings()

        # Redirect stdout to our console
        self.stdout_original = sys.stdout
        sys.stdout = self

        # Initial log message
        self.log("Racing Console started")

    def create_custom_style(self):
        """Create custom styles for the application"""
        style = ttk.Style()

        # Configure the theme
        style.theme_use("clam")

        # Configure frame styles
        style.configure("Racing.TFrame", background=COLOR_THEME["background"])
        style.configure("Racing.TLabelframe", background=COLOR_THEME["background"],
                       foreground=COLOR_THEME["foreground"])
        style.configure("Racing.TLabelframe.Label", background=COLOR_THEME["background"],
                       foreground=COLOR_THEME["accent1"], font=("Arial", 10, "bold"))

        # Configure button styles
        style.configure("Racing.TButton", background=COLOR_THEME["accent2"],
                       foreground=COLOR_THEME["foreground"])
        style.map("Racing.TButton",
                 background=[("active", COLOR_THEME["accent1"])],
                 foreground=[("active", COLOR_THEME["background"])])

        # Configure label styles
        style.configure("Racing.TLabel", background=COLOR_THEME["background"],
                       foreground=COLOR_THEME["foreground"])
        style.configure("Header.TLabel", background=COLOR_THEME["background"],
                       foreground=COLOR_THEME["accent1"], font=("Arial", 14, "bold"))
        style.configure("Version.TLabel", background=COLOR_THEME["background"],
                       foreground=COLOR_THEME["foreground"], font=("Arial", 10))

        # Configure status styles
        style.configure("Running.TLabel", foreground=COLOR_THEME["running"])
        style.configure("Stopped.TLabel", foreground=COLOR_THEME["stopped"])
        style.configure("Warning.TLabel", foreground=COLOR_THEME["warning"])

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
                    "log_file": "racing_console.log",
                    "log_file_size": "1000000"
                },
                "Privacy": {
                    "process_car_setup": "False"
                },
                "Forwarding": {
                    "target_moza": "localhost:22024",
                    "target_sec_mon": "localhost:22025"
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

    def setup_subapps(self):
        """Set up the hard-coded sub-apps"""
        # Define our racing-related sub-apps
        self.subapps = {
            "telemetry": SubApp(
                name="telemetry",
                app_path="telemetry_service.py",
                display_name="Server",
                start_by_default=True,
                console_app=self
            ),
            "dashboard": SubApp(
                name="dashboard",
                app_path="racing_dashboard.py",
                display_name="Racing Dashboard",
                start_by_default=False,
                console_app=self
            ),
        }

        # Create UI for each subapp
        for i, (name, subapp) in enumerate(self.subapps.items()):
            frame = ttk.Frame(self.subapps_frame, style="Racing.TFrame")
            frame.grid(row=0, column=i, padx=15, pady=5)

            # Add controls for this subapp
            label = ttk.Label(frame, text=f"{subapp.display_name}:", style="Racing.TLabel")
            label.grid(row=0, column=0, padx=5, pady=5)

            status_label = ttk.Label(frame, textvariable=subapp.status_var, width=10, style="Stopped.TLabel")
            status_label.grid(row=0, column=1, padx=5, pady=5)

            # Configure status label colors based on status
            def update_status_style(status_var, label):
                status = status_var.get()
                if status == "Running":
                    label.configure(style="Running.TLabel")
                elif status == "Stopped":
                    label.configure(style="Stopped.TLabel")
                else:  # Error or other states
                    label.configure(style="Warning.TLabel")

            # Initial color update
            update_status_style(subapp.status_var, status_label)

            # Set up a trace on the status variable to update styles
            subapp.status_var.trace_add("write", lambda *args, sv=subapp.status_var, lbl=status_label:
                                       update_status_style(sv, lbl))

            start_button = ttk.Button(frame, text="Start", command=lambda s=subapp: s.start(), style="Racing.TButton")
            start_button.grid(row=0, column=2, padx=5, pady=5)

            stop_button = ttk.Button(frame, text="Stop", command=lambda s=subapp: s.stop(), style="Racing.TButton")
            stop_button.grid(row=0, column=3, padx=5, pady=5)

    def setup_header(self):
        # App info section with racing theme
        info_frame = ttk.Frame(self.header_frame, style="Racing.TFrame")
        info_frame.pack(side=tk.LEFT)

        # Create a simple racing flag icon
        # TODO - replace with app icon
        canvas = tk.Canvas(info_frame, width=40, height=30, bg=COLOR_THEME["background"],
                          highlightthickness=0)
        canvas.pack(side=tk.LEFT, padx=(0, 10))

        # Draw checkered flag pattern
        square_size = 5
        for i, j in itertools.product(range(6), range(6)):
            color = "white" if (i + j) % 2 == 0 else "black"
            canvas.create_rectangle(
                i * square_size, j * square_size,
                (i+1) * square_size, (j+1) * square_size,
                fill=color, outline=""
            )

        app_label = ttk.Label(info_frame, text=f"{self.app_name}", style="Header.TLabel")
        app_label.pack(side=tk.LEFT)

        version_label = ttk.Label(info_frame, text=f"v{self.version}", style="Version.TLabel")
        version_label.pack(side=tk.LEFT, padx=(5, 0))

        # Buttons section
        buttons_frame = ttk.Frame(self.header_frame, style="Racing.TFrame")
        buttons_frame.pack(side=tk.RIGHT)

        self.settings_button = ttk.Button(buttons_frame, text="Settings",
                                        command=self.open_settings, style="Racing.TButton")
        self.settings_button.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_button = ttk.Button(buttons_frame, text="Clear Log",
                                     command=self.clear_log, style="Racing.TButton")
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(buttons_frame, text="Save Log",
                                    command=self.save_log, style="Racing.TButton")
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))

        self.test_button = ttk.Button(buttons_frame, text="Test Log",
                                    command=self.test_log, style="Racing.TButton")
        self.test_button.pack(side=tk.LEFT)

    def setup_console(self):
        # Create a text widget for the console with racing theme
        self.console = tk.Text(self.console_frame, wrap=tk.WORD,
                             bg=COLOR_THEME["console_bg"],
                             fg=COLOR_THEME["console_fg"],
                             insertbackground=COLOR_THEME["console_fg"],
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
            filename = f"racing_console_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(self.console.get(1.0, tk.END))
            self.log(f"Log saved to {filename}")
        except Exception as e:
            self.log(f"Error saving log: {e}")

    def test_log(self):
        """Add some test log entries"""
        self.log("Testing telemetry connection...")
        self.log("Connection established on port 20777")
        self.log("Receiving packets at 60Hz")
        print("Tire temperatures nominal")
        print("Fuel remaining: 45.2 liters")

    def open_settings(self):
        """Open the settings window"""
        self.log("Opening settings window")
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
                self.log(f"Stopping {subapp.display_name}...")
                subapp.stop()

        sys.stdout = self.stdout_original
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("assets/favicon.ico")  # Set the icon for the main window
    app = RacingConsoleApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()