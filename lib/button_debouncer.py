# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import time

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

class ButtonDebouncer:
    """
    Class for debouncing button presses.
    """
    def __init__(self, debounce_time=0.3) -> None:
        """
        Initialise the button debouncer.

        Args:
            debounce_time (float): Time in seconds to debounce button presses.
        """
        self.debounce_time = debounce_time  # Time in seconds
        self.last_press_times = {}  # Dictionary to store the last press time for each button

    def onButtonPress(self, button_id) -> bool:
        """
        Called when a button press event occurs.

        Args:
            button_id (str): Unique identifier for the button.

        Returns:
            bool: True if the event should be processed, False otherwise.
        """
        current_time = time.time()
        last_press_time = self.last_press_times.get(button_id, 0)

        # Check if the button press is within the debounce period
        if current_time - last_press_time > self.debounce_time:
            self.last_press_times[button_id] = current_time
            return True
        return False
