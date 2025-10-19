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

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseAPI(ABC):
    """Base class representing all API classes. Derived classes MUST implement toJSON"""
    def _getValueOrDefaultValue(
        self,
        value: Optional[Any],
        default_value: str ='---') -> Optional[Any]:
        """
        Get value or default as string.

        Args:
            value: The value to check.
            default_value (str, optional): Default value if the input is None. Defaults to '---'.

        Returns:
            str: The value as is or default string if None.
        """
        return value if value is not None else default_value

    @abstractmethod
    def toJSON(self) -> Dict[str, Any]:
        """Converts the object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement toJSON()")
