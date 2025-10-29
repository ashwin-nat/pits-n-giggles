import datetime
import glob
import os
import shutil
import sys
import webbrowser

def get_timestamp():
    return datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")

def _cleanup_old_coverage():
    """Remove old .coverage data files and previous HTML reports."""
    for file in glob.glob(".coverage*"):
        try:
            os.remove(file)
        except OSError:
            pass

    if os.path.isdir("htmlcov"):
        shutil.rmtree("htmlcov", ignore_errors=True)

def run_coverage(RUN_TYPE, script, rcfile, script_args_str="", manage_coverage=True, show_report=False):
    _cleanup_old_coverage()
    start_time = datetime.datetime.now()

    timestamp = start_time.strftime("%Y_%m_%d__%H_%M_%S")

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

    if show_report:
        os.system("coverage report")
        report_path = os.path.abspath("htmlcov/index.html")
        webbrowser.open(f"file://{report_path}", new=2)

    elapsed = datetime.datetime.now() - start_time
    print(f"Elapsed time: {elapsed}")
