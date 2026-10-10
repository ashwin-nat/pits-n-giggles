
# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import argparse
import os
import sys

from lib.config import PngSettings
from lib.config.io.json import save_config_to_json

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

DEFAULT_FILE_NAME = "png_config.json"
EXIT_OK = 0
EXIT_FILE_EXISTS = 2

# -------------------------------------- MAIN --------------------------------------------------------------------------

def main(file_name: str = DEFAULT_FILE_NAME, force: bool = False) -> int:
    """Write a default config file. Returns the process exit code.

    Args:
        file_name (str): Output file path.
        force (bool): Overwrite the file if it already exists.
    """
    if os.path.exists(file_name) and not force:
        print(f"Error: '{file_name}' already exists. Use --force to overwrite.", file=sys.stderr)
        return EXIT_FILE_EXISTS

    save_config_to_json(PngSettings(), file_name)
    print(f"Default config written to {file_name}")
    return EXIT_OK

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a default config file")
    parser.add_argument("--file-name", default=DEFAULT_FILE_NAME, help=f"Output file (default: {DEFAULT_FILE_NAME})")
    parser.add_argument("--force", action="store_true", help="Overwrite the file if it already exists")
    cli_args = parser.parse_args()
    sys.exit(main(cli_args.file_name, cli_args.force))
