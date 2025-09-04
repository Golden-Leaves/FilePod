from datetime import datetime,timezone,timedelta
from flask import (Flask, abort, render_template, redirect, url_for, flash,
                   session,request,Blueprint,send_from_directory,jsonify)
from flask_session import Session
from flask_bootstrap5 import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,ForeignKey
from functools import wraps
import zipfile,os
from dotenv import load_dotenv
import secrets
import tempfile
from werkzeug.utils import secure_filename
from helpers.mime_categorizer import categorize_file
from helpers.general import format_file_size,sanitize_rel_path,get_children
from forms import UploadFileForm
from models import db,File

DEFAULT_ROOM_TOKEN = "default_room"
DEFAULT_TTL = timedelta(hours=1)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),".env")
load_dotenv(env_path)
app = Flask(__name__,static_folder="static",template_folder="templates")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "storage",DEFAULT_ROOM_TOKEN) #TODO: Add a real room token
app.jinja_env.filters["format_filesize"] = format_file_size #Sets a sort of function that jinja can use
Bootstrap(app)
Session(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'

db.init_app(app)

with app.app_context():
    db.create_all()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
@app.route("/room/<room_token>/<token>",methods=["GET","POST"])
def room(room_token,token):
    current_folder = request.args.get("current_folder","")
    
    form = UploadFileForm()
    room_token = DEFAULT_ROOM_TOKEN
    #Make sure files are not expired
    # uploaded_files:File = db.session.execute(db.select(File).where(File.expires_at > now)
    
    #Gets all the subfolders and files of the current folder
    subfolders, files,rel_paths = get_children(token=token,room_token=room_token,
                                    current_folder=current_folder) 
    print(subfolders,[file.name for file in files],rel_paths)
    return render_template("room.html",form=form,subfolders=subfolders,files=files,room_token=room_token,token=token)

@app.route("/room-stable")
def room_stable():
    room_token = DEFAULT_ROOM_TOKEN
    form = UploadFileForm()
    now = datetime.now(timezone.utc)
    #Make sure files are not expired
    
    uploaded_files:File = db.session.execute(db.select(File).where(File.expires_at > now)).scalars().all()
    return render_template("room-stable.html",form=form,uploaded_files=uploaded_files,room_token=room_token)

@app.route("/upload/<room_token>/<token>",methods=["POST"])
def upload(room_token,token):
    """Uploads the file to a storage folder and saves metadata to db"""
    is_debug = request.args.get("debug","false").lower() == "true"
    form = UploadFileForm()
    if form.validate_on_submit():
        files = request.files.getlist("files")
        print(files)
        token = secrets.token_urlsafe(16) 

        for f in files:
            if not f:
                flash("No file was selected")
                continue
                
            rel_path = sanitize_rel_path(f.filename)
            print("Relative Path: ",rel_path)
            parent_folder = os.path.dirname(rel_path)
            print("Parent Folder: ",parent_folder)
            filename = os.path.basename(rel_path)
            print(filename)
            
            storage_dir = os.path.join(app.config["UPLOAD_FOLDER"],token) #Will be stored in the storage directory with it's associated token
            os.makedirs(storage_dir,exist_ok=True)
            
            parts = rel_path.split("/") #Windows shenanigans
            
            stored_path = os.path.join(storage_dir,*parts) #Preserve folder structure by using rel_path
            print("Stored Path: ",stored_path)
            os.makedirs(os.path.dirname(stored_path),exist_ok=True) #Make all the parent dirs of stored_path
            f.save(stored_path) 

            file = File()
            file.token = token
            file.name = filename
            file.stored_path = stored_path
            file.size = os.path.getsize(stored_path) #File size in Bytes
            file.mime = f.mimetype
            file.type = categorize_file(file_path=stored_path) #Simplified file type
            file.created_at = datetime.now(timezone.utc)
            file.expires_at = datetime.now(timezone.utc) + DEFAULT_TTL #default TTL for now
            file.rel_path = rel_path
            file.parent_folder = parent_folder
            file.room_token = DEFAULT_ROOM_TOKEN
            
            db.session.add(file)
        db.session.commit()
    if is_debug:
        return redirect(url_for("room_stable"))
    else:
        return redirect(url_for("room",room_token=room_token,token="all"))

@app.route("/files")
def files(): 
    """Returns a JSON of File objects"""
    now = datetime.now(timezone.utc)
    rows:File = db.session.execute(db.select(File).where(File.expires_at > now)).scalars().all()
    payload = []
    for row in rows:
       payload.append({
            "token": row.token,
            "name": row.name,
            "size": row.size,
            "type": row.type,
            "expires_at": row.expires_at.isoformat(),
            "download_count": row.download_count,
        })
    return "This path is deprecated"


@app.route("/download/<room_token>/<token>/<path:filename>")
def download(token,filename):
    """Download desired files/folders"""
    filename = secure_filename(filename)
    downloaded_files:File = db.session.execute(db.select(File).where(File.token == token)).scalars().all()
    storage_dir = os.path.join(app.config["UPLOAD_FOLDER"],token)
    temp_dir = tempfile.gettempdir() #Gets the system's temp dir(Cross-platform)
    zip_path = os.path.join(temp_dir,f"{token}.zip")
    
    if len(downloaded_files) > 1: #Zips the folderif more than one file
        os.makedirs("temp/archive", exist_ok=True)
        with zipfile.ZipFile(zip_path,mode="w") as zf:
            #Traverses every file in the dir and writes to a zip
            for root, _ , files in os.walk(storage_dir):
                for file in files:
                    abs_file_path = os.path.join(root,file)
                    #Only trims to storage path, so it doesn't leak the full directory path
                    rel_file_path = os.path.relpath(abs_file_path,storage_dir)
                    print(rel_file_path)
                    zf.write(abs_file_path,rel_file_path)
        return send_from_directory(directory=os.path.dirname(zip_path),path=os.path.basename(zip_path),
                                   as_attachment=True,download_name=filename)
    else:
        return send_from_directory(directory=storage_dir,path=filename,as_attachment=True,
                                   download_name=filename)
        
        
@app.route("/test")
def test():
    current_folder = request.args.get("current_folder","")
    token = request.args.get("token","all")
    subfolders,files,rel_paths = get_children(token=token, current_folder=current_folder, room_token=DEFAULT_ROOM_TOKEN)
    print("subfolders sample:", subfolders[:1])
    print("files sample:", files[:1])
    print("rel_paths sample:", rel_paths[:1])
    print("types:", type(subfolders[0]), type(files[0]) if files else None, type(rel_paths[0]) if rel_paths else None)
    return jsonify({
        "subfolders": [
            {
                "name": sf["name"],
                "token": sf["token"],
                "path": sf["path"]
            } for sf in subfolders
        ],
        "files": [file.name for file in files],
        "rel_paths": rel_paths
            
        
    })

if __name__ == "__main__":
    app.run(debug=True)