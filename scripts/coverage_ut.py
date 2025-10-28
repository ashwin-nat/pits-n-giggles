import os
import sys

# Add project root to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.coverage_base import run_coverage

is_ci = "--ci" in sys.argv

run_coverage(
    RUN_TYPE="unit",
    args_str="--rcfile=scripts/.coveragerc_ut",
    script="tests/unit_tests.py",
    show_report=not is_ci)
