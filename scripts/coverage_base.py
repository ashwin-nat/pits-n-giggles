import os
import datetime
import webbrowser

def run_coverage(RUN_TYPE, cov_args_str, script, script_args_str="", show_report=False):

    RUN_TYPE = "integration"
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
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

    return

if __name__ == "__main__":
    raise SystemExit("This is a library, not a script.")
