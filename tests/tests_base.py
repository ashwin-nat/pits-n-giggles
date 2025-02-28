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
# pylint: skip-file

import unittest
import os
from colorama import Fore, Style
import sys
import json
from deepdiff import DeepDiff

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ----------------------------------------------------------------------------------------------------------------------

class CustomTestResult(unittest.TextTestResult):
    """Class to format test results in color
    """
    def startTest(self, test):
        super().startTest(test)
        test_class_name = test.getFullTestName()
        test_description = test.shortDescription()

        # Split the class name by dots and color each part differently
        class_parts = test_class_name.split('.')
        colored_parts = []
        colors = [
            Fore.CYAN,
            Fore.MAGENTA,
            Fore.GREEN,
            Fore.BLUE,
            Fore.RED,
        ]  # Add more colors if needed

        for i, part in enumerate(class_parts):
            color = colors[i % len(colors)]  # Cycle through colors if there are more parts than colors
            colored_parts.append(f"{color}{Style.BRIGHT}{part}")

        # Join the colored parts with dots
        colored_class_name = f"{Fore.WHITE}{Style.BRIGHT}.{Style.RESET_ALL}".join(colored_parts)

        print(f"{Fore.MAGENTA}{Style.BRIGHT}Running test: "
            f"{colored_class_name}.{Fore.YELLOW}{Style.BRIGHT}{test_description}", end="")

    def addSuccess(self, test):
        super().addSuccess(test)
        print(f" {Fore.GREEN}[PASS]{Style.RESET_ALL}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f" {Fore.RED}[FAIL]{Style.RESET_ALL}")

    def addError(self, test, err):
        super().addError(test, err)
        print(f" {Fore.RED}[ERROR]{Style.RESET_ALL}")

class F1TelemetryUnitTestsBase(unittest.TestCase):
    """
    Base class for all unit tests.
    """
    def shortDescription(self):
        return self._testMethodName

    def getFullTestName(self):
        test_class = self.__class__
        test_hierarchy = [test_class.__name__]

        while issubclass(test_class, unittest.TestCase):
            parent_class = test_class.__bases__[0]
            if issubclass(parent_class, unittest.TestCase):
                if parent_class.__name__ == 'F1TelemetryUnitTestsBase':
                    break
                test_hierarchy.insert(0, parent_class.__name__)
            test_class = parent_class

        return '.'.join(test_hierarchy)

    def jsonComparisionUtil(self, expected_json, actual_json) -> None:
        """
        Compares two JSON objects and prints differences if they are not equal.

        Args:
            expected_json (dict): The expected JSON object.
            actual_json (dict): The actual JSON object to compare.

        Raises:
            AssertionError: If the two JSON objects are not equal.
        """
        differences = DeepDiff(expected_json, actual_json, ignore_order=True)

        if differences:
            print("Differences found:")
            if 'values_changed' in differences:
                for key, change in differences['values_changed'].items():
                    # Extract the key name and expected/actual values
                    key_name = key.replace("root", "").strip("[]'")  # Clean up the key name
                    expected_value = change['old_value']
                    actual_value = change['new_value']
                    print(f"Changed key: {key_name}  Expected value: {expected_value}  Actual value: {actual_value}")
            else:
                print(json.dumps(differences, indent=4))
            raise AssertionError(f"JSON objects are not equal.\n {json.dumps(differences, indent=4)}")
