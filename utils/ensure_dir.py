from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    folder_path = Path(path)
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path
