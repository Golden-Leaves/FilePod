from werkzeug.utils import secure_filename
from pathlib import Path
def format_file_size(file_size:int) -> str:
    """Converts a byte size into a human-readable format (e.g., 2.3 MB, 45.1 GB,...)."""
    size_map = {
    "B": 1,
    "KB": 1024,
    "MB": 1024**2,
    "GB": 1024**3,
    "TB": 1024**4,
    "PB": 1024**5,
}
    
    for size,bytes in reversed(list(size_map.items())):
        if file_size >= bytes: #If file_size is larger than current size unit
            return f"{file_size / bytes:.1f} {size}"
    return f"{file_size} B"
def is_folder_upload(files:list):
    """Detects if the current batch that was uploaded is a folder"""
    # folders contain slash in filename, plain multi-file picks do not
    for f in files:
        name = (f.filename or "").replace("\\", "/")
        if "/" in name:
            return True
    return False

def sanitize_rel_path(raw: str) -> str:
    """secure_file_name() strips directory structure, use this isntead for directories"""
    raw = (raw or "").replace("\\", "/")
    parts = [p for p in raw.split("/") if p not in ("", ".", "..")]
    safe_parts = [secure_filename(p) for p in parts if secure_filename(p)]
    return Path("/".join(safe_parts)).as_posix()

if __name__ == "__main__":
    print(format_file_size(1024*2))
    print([])