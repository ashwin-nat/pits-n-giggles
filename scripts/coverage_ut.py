import os
import webbrowser

status = os.system("coverage run --rcfile=scripts/.coveragerc_ut tests/unit_tests.py")
if status != 0:
    print("Unit tests failed")
    exit(status)

os.system("coverage report")
report_path = os.path.abspath("htmlcov/index.html")
webbrowser.open(f"file://{report_path}", new=2)
