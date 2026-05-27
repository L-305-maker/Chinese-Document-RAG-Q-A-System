import json


def read_data(file_path: str):
    data = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"Line {line_no} JSON parse failed: {exc}")

    return data
