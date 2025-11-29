import datetime
import glob
import os
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
        cmd = f"coverage run --rcfile={rcfile} {script} {script_args_str}"
    else:
        cmd = f"{sys.executable} {script} {script_args_str}"

    print(f"Running command: {cmd}")
    status = os.system(cmd)
    if status != 0:
        print(f"{RUN_TYPE.title()} tests failed with status {status}")

    # CRITICAL: Give subprocesses time to flush coverage data
    print("\nWaiting for coverage data to be written...")
    time.sleep(2)

    # Debug: Check what coverage files exist
    coverage_files = glob.glob(".coverage.*")
    print(f"\nFound {len(coverage_files)} coverage data files:")
    for f in coverage_files:
        size = os.path.getsize(f)
        print(f"  - {f} ({size} bytes)")

    if not coverage_files:
        print("\n  WARNING: No coverage data files found!")
        print("This usually means:")
        print("  1. Subprocesses didn't run under coverage")
        print("  2. Coverage data wasn't flushed before process exit")
        print("  3. Coverage files were created in a different directory")
        return

    # Combine coverage data
    print("\nCombining coverage data...")
    combine_status = os.system("coverage combine")
    if combine_status != 0:
        print(f"  Coverage combine failed with status {combine_status}")
        return

    # Check if .coverage file was created
    if not os.path.exists(".coverage"):
        print("  WARNING: .coverage file not created after combine!")
        return

    combined_size = os.path.getsize(".coverage")
    print(f" Combined coverage data: .coverage ({combined_size} bytes)")

    # Generate HTML report
    title = f"{RUN_TYPE.capitalize()} Test Coverage ({timestamp})"
    print(f"\nGenerating HTML report...")
    html_status = os.system(f'coverage html --title="{title}"')
    if html_status != 0:
        print(f"  Coverage HTML generation failed with status {html_status}")

    # Ensure the coverage_reports directory exists
    os.makedirs("coverage_reports", exist_ok=True)

    # Rename htmlcov folder to include timestamp for archival
    if os.path.isdir("htmlcov"):
        os.rename("htmlcov", htmlcov_dir)
        print(f" Saved HTML report: {htmlcov_dir}/index.html")
    else:
        print("  WARNING: htmlcov directory not created!")

    if show_report:
        print("\nGenerating text report...")
        os.system("coverage report")
        report_path = os.path.abspath(f"{htmlcov_dir}/index.html")
        print(f"\nOpening report in browser: {report_path}")
        webbrowser.open(f"file://{report_path}", new=2)

    elapsed = datetime.datetime.now() - start_time
    print(f"\nElapsed time: {elapsed}")
