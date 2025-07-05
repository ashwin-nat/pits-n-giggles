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

from typing import Any

from pydantic_core import core_schema

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class FilePathStr(str):
    """
    A string type that represents a path to an existing file.

    This type is used in Pydantic models to ensure that a given string
    points to a file that exists on disk. Useful for configuration paths
    like certificates, keys, or any file inputs the user must provide.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, __source_type, __handler) -> core_schema.CoreSchema:
        """
        Hook used by Pydantic v2 to define custom validation logic
        for this type.

        Returns:
            CoreSchema: A schema that uses `validate` to check values.
        """
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, value: Any) -> str:
        """
        Validate that the input is a string and that it points to an existing file.

        Args:
            value (Any): The value to validate.

        Returns:
            str: The validated file path.

        Raises:
            TypeError: If the input is not a string.
        """
        if not isinstance(value, str):
            raise TypeError("Expected a string for file path")
        return value
