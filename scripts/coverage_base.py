import datetime
import glob
import os
import shlex
import subprocess
import sys
import time
import webbrowser


def _cleanup_old_coverage():
    """Remove old .coverage data files but keep past HTML reports."""
    for file in glob.glob(".coverage*"):
        try:
            os.remove(file)
            print(f"Removed old coverage file: {file}")
        except OSError as e:
            print(f"Could not remove {file}: {e}")


def run_coverage(RUN_TYPE, script, rcfile, script_args_str="", manage_coverage=True, show_report=False):
    _cleanup_old_coverage()
    start_time = datetime.datetime.now()

    timestamp = start_time.strftime("%Y_%m_%d__%H_%M_%S")
    htmlcov_dir = f"coverage_reports/htmlcov_{timestamp}"

    if manage_coverage:
        os.environ["COVERAGE_PROCESS_START"] = rcfile
        cmd_args = ["coverage", "run", f"--rcfile={rcfile}", script] + shlex.split(script_args_str)
    else:
        cmd_args = [sys.executable, script] + shlex.split(script_args_str)

    print(f"Running command: {' '.join(cmd_args)}")
    # cmd_args is built from trusted internal values (script path + args), not user input
    result = subprocess.run(cmd_args)  # noqa: S603
    if result.returncode != 0:
        print(f"{RUN_TYPE.title()} tests failed with status {result.returncode}")

    # CRITICAL: Give subprocesses time to flush coverage data
    print("\nWaiting for coverage data to be written...")
    time.sleep(2)

    # Check for both single-process and multi-process coverage files
    coverage_files = glob.glob(".coverage.*")
    main_coverage = os.path.exists(".coverage")

    print(f"\nCoverage data status:")
    print(f"  - Main .coverage file: {'EXISTS' if main_coverage else 'NOT FOUND'}")
    print(f"  - Subprocess .coverage.* files: {len(coverage_files)} found")

    if coverage_files:
        for f in coverage_files:
            size = os.path.getsize(f)
            print(f"  - {f} ({size} bytes)")

    # Handle different coverage scenarios
    if not main_coverage and not coverage_files:
        print("\nWARNING: No coverage data files found!")
        print("This usually means:")
        print("  1. Subprocesses didn't run under coverage")
        print("  2. Coverage data wasn't flushed before process exit")
        print("  3. Coverage files were created in a different directory")
        return

    # If we have subprocess files, combine them
    if coverage_files:
        print("\nCombining coverage data from multiple processes...")
        combine_result = subprocess.run(["coverage", "combine"])
        if combine_result.returncode != 0:
            print(f"  WARNING: Coverage combine failed with status {combine_result.returncode}")
            return

        # Verify .coverage file was created after combine
        if not os.path.exists(".coverage"):
            print("  WARNING: .coverage file not created after combine!")
            return
    elif main_coverage:
        print("\nSingle-process coverage data found (no combine needed)")

    # Check final .coverage file
    if os.path.exists(".coverage"):
        combined_size = os.path.getsize(".coverage")
        print(f"Final coverage data: .coverage ({combined_size} bytes)")
    else:
        print("ERROR: No .coverage file available for report generation!")
        return

    # Generate HTML report
    title = f"{RUN_TYPE.capitalize()} Test Coverage ({timestamp})"
    print(f"\nGenerating HTML report...")
    html_result = subprocess.run(["coverage", "html", f"--title={title}"])
    if html_result.returncode != 0:
        print(f"  WARNING: Coverage HTML generation failed with status {html_result.returncode}")
        return

    # Ensure the coverage_reports directory exists
    os.makedirs("coverage_reports", exist_ok=True)

    # Rename htmlcov folder to include timestamp for archival
    if os.path.isdir("htmlcov"):
        os.rename("htmlcov", htmlcov_dir)
        print(f"Saved HTML report: {htmlcov_dir}/index.html")
    else:
        print("  WARNING: htmlcov directory not created!")
        return

    if show_report:
        print("\nGenerating text report...")
        subprocess.run(["coverage", "report"])
        report_path = os.path.abspath(f"{htmlcov_dir}/index.html")
        print(f"\nOpening report in browser: {report_path}")
        webbrowser.open(f"file://{report_path}", new=2)

    elapsed = datetime.datetime.now() - start_time
    print(f"\nElapsed time: {elapsed}")
