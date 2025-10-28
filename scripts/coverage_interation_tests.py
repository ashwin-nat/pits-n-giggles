import os
import sys

# Add project root to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.coverage_base import run_coverage

is_ci = "--ci" in sys.argv

run_coverage(
    RUN_TYPE="integration",
    cov_args_str="--rcfile=scripts/.coveragerc_integration",
    script="tests/integration_test/runner.py",
    script_args_str="--coverage --ci" if is_ci else "--coverage",
    show_report=not is_ci
)
