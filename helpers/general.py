
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models import File,db
from datetime import datetime,timezone

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
    """secure_file_name() strips directory structure, use this instead for directories"""
    raw = (raw or "").replace("\\", "/")
    parts = [p for p in raw.split("/") if p not in ("", ".", "..")]
    safe_parts = [secure_filename(p) for p in parts if secure_filename(p)]
    return Path("/".join(safe_parts)).as_posix()

def get_children(token:str,current_folder:str,root:str):
    now = datetime.now(timezone.utc)
    files = (db.session.execute(db.select(File)
            .where(File.expires_at > now, File.parent_folder == current_folder,File.token == token)
            .order_by(File.name.asc()))
            .scalars().all())
    prefix = f"{current_folder}/" if current_folder else "" #Current folder prefix
    #prefix/% or prefix% matches anything that starts with the prefix(cuz of the '%')
    rel_paths = (db.session.execute(db.select(File.rel_path)
                .where(File.expires_at > now,File.rel_path.like(f"{prefix}%"),File.token == token))
                  ).scalars().all()
    
    print(rel_paths)
    return rel_paths
        
if __name__ == "__main__":
    print(format_file_size(1024*2))
    print([])
    get_children(token="abc123", current_folder="Okayu", root="storage")