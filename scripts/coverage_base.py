import datetime
import glob
import os
import sys
import webbrowser

def _cleanup_old_coverage():
    """Remove old .coverage data files but keep past HTML reports."""
    for file in glob.glob(".coverage*"):
        try:
            os.remove(file)
        except OSError:
            pass


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

    print(f"Running command {cmd}")
    status = os.system(cmd)
    if status != 0:
        print(f"{RUN_TYPE.title()} tests failed")

    os.system("coverage combine")
    title = f"{RUN_TYPE.capitalize()} Test Coverage ({timestamp})"
    os.system(f'coverage html --title="{title}"')

    # Ensure the coverage_reports directory exists
    os.makedirs("coverage_reports", exist_ok=True)

    # Rename htmlcov folder to include timestamp for archival
    if os.path.isdir("htmlcov"):
        os.rename("htmlcov", htmlcov_dir)
        print(f"Saved HTML report as: {htmlcov_dir}/index.html")

    if show_report:
        os.system("coverage report")
        report_path = os.path.abspath(f"{htmlcov_dir}/index.html")
        webbrowser.open(f"file://{report_path}", new=2)

    elapsed = datetime.datetime.now() - start_time
    print(f"Elapsed time: {elapsed}")
