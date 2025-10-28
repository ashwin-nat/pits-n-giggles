import os
import webbrowser

status = os.system("coverage run --rcfile=scripts/.coveragerc_integration tests/integration_test/runner.py")
if status != 0:
    print("Integration test failed")
    exit(status)

os.system("coverage report")
report_path = os.path.abspath("htmlcov/index.html")
webbrowser.open(f"file://{report_path}", new=2)
