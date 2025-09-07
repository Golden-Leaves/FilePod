from werkzeug.utils import secure_filename
from pathlib import Path
import os
import shutil
import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ..models import File,db
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
        current_file_size = file_size / bytes #In current units like KB or MB
        if file_size >= bytes: #If file_size is larger than current size unit
            if current_file_size.is_integer():
                return f"{int(current_file_size)} {size}"
            else:
                return f"{current_file_size:.1f} {size}"
           
        
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
    raw = (raw or "").replace("\\", "/") #Web requests always send "/"
    print(f"Raw: {raw}")
    parts = [p for p in raw.split("/") if p not in ("", ".", "..")]
    safe_parts = [secure_filename(p) for p in parts if secure_filename(p)]
    return os.path.join(*safe_parts) if safe_parts else ""

def get_children(room_token:str,token:str,current_folder:str) -> tuple[list[dict[str,str]],File,str]:
    """Gets all the immediate subfolder and child files of the current folder
    current_folder is the relative path of the current folder
    root is jsut te storage_dir
    """
    current_folder = sanitize_rel_path(current_folder)
    subfolders_objs = []
    now = datetime.now(timezone.utc)
    prefix = f"{current_folder}\\" if current_folder else "" #current_folder with a "/" at the end
    base = [File.expires_at > now, File.room_token == room_token]
    if token != "all": #Clicking on subfolders
        base.append(File.token == token)
        
  
    files: list[File] = (db.session.execute(db.select(File)
            .where(*base,File.parent_folder == current_folder)
            .order_by(File.name.asc()))
            .scalars().all()) #"Database1.accdb"
    
    
    if token == "all":
         rel_paths: list[tuple[str,str]] = (db.session.execute(db.select(File.rel_path,File.token) #Note: we also include token here
                .where(*base))
                ).tuples().all() #"some_folder/Misc/Database1.accdb"
    else:
        rel_paths: list[tuple[str,str]] = (db.session.execute(db.select(File.rel_path,File.token) #Note: we also include token here
                    .where(*base,File.rel_path.startswith(prefix)))
                    ).tuples().all() #"some_folder/Misc/Database1.accdb"
    #TODO: Subfolders being detected wrongly
    seen = set() #Checks for duplicate dictionairy entires to skip
    for rel_path,token in rel_paths:
        if rel_path.startswith(prefix): #If the current_folder matches
            tail = rel_path[len(prefix):] #Everything after prefix
            if "\\" in tail:
                #Gets the immediate child folder
                subfolder_name = tail.split("\\", 1)[0] #"some_folder/12312/1231231/file.txt" -> some_folder
                subfolder_token = token
                subfolder_path =  os.path.join(current_folder,subfolder_name) #The relative path of the subfolder
                # immediate child only
                key = (subfolder_name,subfolder_token,subfolder_path)
                if key in seen:
                    continue
                seen.add(key)
                subfolders_objs.append(
                    {
                        "name":subfolder_name,
                        "token":subfolder_token,
                        "path":subfolder_path
                    }
                )
    subfolder_objs = list(sorted(subfolders_objs, key=lambda subfolder:subfolder["name"]))
    return subfolder_objs,files,rel_paths

def get_breadcrumbs(current_folder:str) -> list[dict[str,str]]:
    """Creates 'breadcrumbs' form current_folder path so you can traverse up the folders"""
    #Check out google drive's for reference
    breadcrumbs = []
    #"some_folder/Documents" => ["some_folder", "Documents"] 
    parts = (current_folder or "").strip("/").split("/") #Number of segments in the path
    #NOTE:Breadcrumbs are built from top to bottom
    for i in range(1, len(parts)+1):
        breadcrumb_path = "/".join(parts[:i])  #[a,b,c] = "a" (parent folder path)
        breadcrumb_name = parts[i - 1] #[a,b,c] = "a" (parent folder name)/ current_folder's name
        breadcrumbs.append({
            "name": breadcrumb_name,
            "path": breadcrumb_path
        })
    return breadcrumbs
def cleanup_expired_tokens(storage_dir:str,room_token:str) -> None:
    """Deletes token folders that are already expired"""
    now = datetime.now(timezone.utc)

    expired_tokens = (db.session.execute(db.select(File.token).where(File.expires_at < now,File.room_token == room_token)
                                 .distinct()).scalars().all()) 
    for token in expired_tokens:
        token_folder = os.path.join(storage_dir,room_token,token)
        shutil.rmtree(token_folder,ignore_errors=True) #Deletes the token folder in /storage
        db.session.execute(db.delete(File).where(File.token == token, File.room_token == room_token)) #Deletes rows
                
    db.session.commit()
if __name__ == "__main__":
    print(format_file_size(1024*2))
    print([])
    get_children(token="abc123", current_folder="some_folder/Documents", root="storage")