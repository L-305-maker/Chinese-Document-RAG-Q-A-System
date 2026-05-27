from pathlib import Path

def ensure_dir(file_path:str):
    folder_path = Path(file_path)
    if not folder_path.exists():
        folder_path.mkdir(parents=True,exist_ok=True)
