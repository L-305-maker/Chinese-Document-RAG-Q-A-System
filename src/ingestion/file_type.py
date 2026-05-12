from pathlib import Path

def type_file(file_Path:str)->str:
    suffix = Path(file_Path).suffix.lower()

    if suffix == ".pdf":
        return "pdf"
    
    elif suffix == ".txt":
        return "txt"
    
    elif suffix == ".md":
        return "markdown"
    
    elif suffix in [".docx",".doc"]:
        return "word"
    
    else:
        raise ValueError(f"Supposed file type:{file_Path}")