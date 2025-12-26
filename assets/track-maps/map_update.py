from pathlib import Path

OLD = 'stroke="black" stroke-width="2"'
NEW = 'stroke="white" stroke-width="4"'

svg_files = list(Path(".").glob("*.svg"))

if not svg_files:
    print("No SVG files found in current directory.")
    exit(0)

modified_count = 0

for svg_path in svg_files:
    content = svg_path.read_text(encoding="utf-8")

    if OLD not in content:
        print(f"[-] No match in: {svg_path.name}")
        continue

    updated = content.replace(OLD, NEW)
    svg_path.write_text(updated, encoding="utf-8")

    print(f"Updated: {svg_path.name}")
    modified_count += 1

print(f"\nDone. Modified {modified_count} file(s).")

