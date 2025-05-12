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

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Define all color schemes
_THEMES = {
    "racing": {
        "background": "#1E1E1E",       # Dark background
        "foreground": "#E0E0E0",       # Light text
        "accent1": "#FF2800",          # Racing red
        "accent2": "#303030",          # Dark gray
        "console_bg": "#000000",       # Console black
        "console_fg": "#FFFFFF",       # Terminal white
        "running": "#2E8B57",          # Sea Green for running status
        "stopped": "#FF2800",          # Red for stopped status
        "warning": "#FFA500",          # Orange for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "midnight_blue": {
        "background": "#1A1B26",       # Deep blue-black background
        "foreground": "#D8DEE9",       # Ice blue text
        "accent1": "#7AA2F7",          # Bright blue accent
        "accent2": "#24283B",          # Slightly lighter background for buttons
        "console_bg": "#16161E",       # Even darker console
        "console_fg": "#E0E0E0",       # Light gray text for better eye comfort
        "running": "#9ECE6A",          # Soft green for running status
        "stopped": "#F7768E",          # Soft red for stopped status
        "warning": "#E0AF68",          # Amber for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "dark_teal": {
        "background": "#0F111A",       # Very dark background
        "foreground": "#ECEFF4",       # Crisp white text
        "accent1": "#00B8A3",          # Teal accent
        "accent2": "#232731",          # Slightly lighter buttons
        "console_bg": "#000000",       # Black console
        "console_fg": "#F8F8F2",       # Off-white console text
        "running": "#26C99E",          # Bright teal for running
        "stopped": "#FF5370",          # Coral red for stopped
        "warning": "#FFCB6B",          # Bright yellow for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "graphite": {
        "background": "#282C34",       # Dark charcoal background
        "foreground": "#E5E9F0",       # Very light gray text
        "accent1": "#61AFEF",          # Sky blue accent
        "accent2": "#3E4452",          # Medium dark gray for buttons
        "console_bg": "#21252B",       # Slightly lighter console background
        "console_fg": "#FFFFFF",       # Pure white console text
        "running": "#98C379",          # Muted green for running
        "stopped": "#E06C75",          # Soft red for stopped
        "warning": "#D19A66",          # Soft orange for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "purple_night": {
        "background": "#292D3E",       # Dark purple-blue background
        "foreground": "#D0D0D0",       # Light gray text
        "accent1": "#C792EA",          # Lavender purple accent
        "accent2": "#3A3F58",          # Lighter background for contrast
        "console_bg": "#1A1C2C",       # Very dark blue console
        "console_fg": "#EEFFFF",       # Very light blue-white text
        "running": "#82AAFF",          # Bright blue for running
        "stopped": "#F07178",          # Coral for stopped
        "warning": "#FFCB6B",          # Gold for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "carbon": {
        "background": "#1D1F21",       # Very dark gray background
        "foreground": "#F0F0F0",       # Very light gray text (high contrast)
        "accent1": "#4D9DE0",          # Strong blue accent
        "accent2": "#2D2F31",          # Slightly lighter buttons
        "console_bg": "#000000",       # Black console
        "console_fg": "#FFFFFF",       # White console text (maximum contrast)
        "running": "#56B366",          # Vivid green for running
        "stopped": "#E45649",          # Vivid red for stopped
        "warning": "#E5C07B",          # Soft gold for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "oceanic": {
        "background": "#1B2B34",       # Deep ocean blue background
        "foreground": "#D8DEE9",       # Ice blue text
        "accent1": "#5FB3B3",          # Seafoam accent
        "accent2": "#2D3C45",          # Slightly lighter background for contrast
        "console_bg": "#0F1419",       # Nearly black console
        "console_fg": "#FAFAFA",       # Almost white text
        "running": "#99C794",          # Soft green for running status
        "stopped": "#EC5F67",          # Coral red for stopped status
        "warning": "#FAC863",          # Warm yellow for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "azure_night": {
        "background": "#15232D",       # Dark azure background
        "foreground": "#E7F1F5",       # Very light blue-white text
        "accent1": "#4990E2",          # Vibrant azure accent
        "accent2": "#213440",          # Lighter background for elements
        "console_bg": "#0D1B26",       # Very dark console
        "console_fg": "#F0F7FA",       # Ice white console text
        "running": "#7ED321",          # Bright green for running
        "stopped": "#FF5252",          # Bright red for stopped
        "warning": "#FFCA28",          # Rich amber for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "cobalt": {
        "background": "#193549",       # Deep cobalt blue
        "foreground": "#FFFFFF",       # Pure white text for maximum contrast
        "accent1": "#FF9D00",          # Vibrant orange accent
        "accent2": "#2C4A63",          # Lighter cobalt for buttons
        "console_bg": "#0D2138",       # Very dark blue console
        "console_fg": "#FFFFFF",       # White text
        "running": "#3AD900",          # Bright lime green for running
        "stopped": "#FF2600",          # Vivid red for stopped
        "warning": "#FFC600",          # Bright yellow for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "deep_ocean": {
        "background": "#091B2E",       # Very dark blue-teal
        "foreground": "#E6F5F5",       # Light teal-white
        "accent1": "#25C0F0",          # Electric blue accent
        "accent2": "#14293D",          # Slightly lighter background
        "console_bg": "#051019",       # Nearly black console
        "console_fg": "#F2FDFF",       # Very light blue-white text
        "running": "#00E3C0",          # Bright teal for running
        "stopped": "#FF6B7F",          # Soft coral for stopped
        "warning": "#FFD166",          # Soft yellow for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "emerald_dark": {
        "background": "#0C1F17",       # Very dark forest green
        "foreground": "#E3FCEF",       # Light minty text
        "accent1": "#08C49C",          # Bright emerald accent
        "accent2": "#182F25",          # Slightly lighter background
        "console_bg": "#071A12",       # Almost black console with green tint
        "console_fg": "#F0FFF9",       # Near-white with slight green tint
        "running": "#5DE3A5",          # Bright emerald green for running
        "stopped": "#FF6B6B",          # Soft red for stopped
        "warning": "#FFD166",          # Golden yellow for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "nordic_fjord": {
        "background": "#0F1C2D",       # Deep blue-teal background
        "foreground": "#ECEFF4",       # Snow white text
        "accent1": "#88C0D0",          # Soft arctic blue accent
        "accent2": "#1D2C3F",          # Lighter fjord blue for elements
        "console_bg": "#0A1423",       # Very dark blue console
        "console_fg": "#E5E9F0",       # Arctic white console text
        "running": "#A3BE8C",          # Moss green for running
        "stopped": "#BF616A",          # Soft red for stopped
        "warning": "#EBCB8B",          # Muted gold for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "deep_horizon": {
        "background": "#1A2B3C",       # Deep blue-teal background
        "foreground": "#E6F0F5",       # Icy blue-white text
        "accent1": "#55B6C2",          # Medium teal accent
        "accent2": "#263545",          # Slightly lighter background for contrast
        "console_bg": "#121E2A",       # Very dark blue console
        "console_fg": "#F0F8FA",       # Very light blue-white text
        "running": "#73C990",          # Soft teal-green for running
        "stopped": "#E05252",          # Medium red for stopped
        "warning": "#E6C454",          # Gold for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
    "arctic_night": {
        "background": "#151C25",       # Very dark bluish background
        "foreground": "#D4E5F2",       # Light blue-white text
        "accent1": "#45A9A5",          # Medium blue-teal accent
        "accent2": "#1F2835",          # Slightly lighter buttons
        "console_bg": "#0D131A",       # Nearly black console
        "console_fg": "#E5EEF5",       # Very light icy text
        "running": "#4CAF50",          # Faded green for running
        "stopped": "#DB5860",          # Deep red for stopped
        "warning": "#DDA448",          # Dark amber for warnings
        "disabled_bg": "#808080",      # Gray for disabled elements
        "disabled_text": "#FFFFFF",    # White for disabled text
    },
}

# Use this as your color scheme
COLOUR_SCHEME = _THEMES["arctic_night"]
