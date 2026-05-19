# tests_wdt.py conflicts with the tests_wdt/ package (same base name).
# The package supersedes the file; exclude the file so pytest doesn't choke.
collect_ignore = ["tests_wdt.py"]
