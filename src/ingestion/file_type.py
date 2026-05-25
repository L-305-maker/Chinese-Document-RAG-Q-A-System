from pathlib import Path


#用于判断文件类型，若非适配文件类型，则抛出异常
def detect_file_type(file_Path:str)->str:
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
        raise ValueError(f"Unsupposed file type:{file_Path}")