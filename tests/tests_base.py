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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ----------------------------------------------------------------------------------------------------------------------

class CustomTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        test_class_name = test.getFullTestName()
        test_description = test.shortDescription()
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Running test: {Fore.CYAN}{Style.BRIGHT}"
              f"{test_class_name}.{Fore.YELLOW}{Style.BRIGHT}{test_description}", end="")

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