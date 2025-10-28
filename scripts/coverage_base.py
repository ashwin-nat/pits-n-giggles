import datetime
import glob
import os
import shutil
import webbrowser


def _cleanup_old_coverage():
    """Remove old .coverage data files and previous HTML reports."""
    for file in glob.glob(".coverage*"):
        try:
            os.remove(file)
        except OSError:
            pass

    if os.path.isdir("htmlcov"):
        shutil.rmtree("htmlcov", ignore_errors=True)

def run_coverage(RUN_TYPE, cov_args_str, script, script_args_str="", show_report=False):
    _cleanup_old_coverage()
    start_time = datetime.datetime.now()

    RUN_TYPE = "integration"
    timestamp = start_time.strftime("%Y_%m_%d__%H_%M_%S")
    data_file = f".coverage_{RUN_TYPE}_{timestamp}"

    # Run coverage with named data file
    status = os.system(f"coverage run --data-file={data_file} {cov_args_str} {script} {script_args_str}")
    if status != 0:
        print(f"{RUN_TYPE.title()} tests failed")
        raise SystemExit(status)

    # Combine and generate HTML report
    os.system(f"coverage combine {data_file}")
    title = f"{RUN_TYPE.capitalize()} Test Coverage ({timestamp})"
    os.system(f'coverage html --title="{title}"')

    if not show_report:
        return

    # Print summary in console
    os.system("coverage report")

    # Open HTML report
    report_path = os.path.abspath("htmlcov/index.html")
    webbrowser.open(f"file://{report_path}", new=2)

    end_time = datetime.datetime.now()
    elapsed_time = end_time - start_time
    total_seconds = int(elapsed_time.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(elapsed_time.microseconds / 1000)

    print(f"Elapsed time: {hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}")

    return

if __name__ == "__main__":
    raise SystemExit("This is a library, not a script.")
