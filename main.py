import os
from datetime import datetime,timezone,timedelta
from flask import (Flask, abort, render_template, redirect, url_for, flash,
                   session,request,Blueprint,send_from_directory,jsonify,send_file)
from flask_session import Session
from flask_bootstrap5 import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import zipfile
from dotenv import load_dotenv
import secrets
import tempfile
from werkzeug.utils import safe_join
import time
from helpers.mime_categorizer import categorize_file
from helpers.general import format_file_size,sanitize_rel_path,get_children,get_breadcrumbs,cleanup_expired_tokens
from forms import UploadFileForm
from models import db,File

DEFAULT_ROOM_TOKEN = "default_room"
# DEFAULT_TTL = timedelta(hours=1)
DEFAULT_TTL = timedelta(seconds=5)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),".env")
load_dotenv(env_path)
app = Flask(__name__,static_folder="static",template_folder="templates")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "storage") #TODO: Add a real room token
app.jinja_env.filters["format_filesize"] = format_file_size #Sets a sort of function that jinja can use
Bootstrap(app)
Session(app)

normalize = lambda x: x.replace("\\","/")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'

db.init_app(app)

with app.app_context():
    db.create_all()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
@app.route("/room/<room_token>/<token>",methods=["GET","POST"])
def room(room_token,token):
    current_folder = request.args.get("current_folder","")
    cleanup_expired_tokens(app.config["UPLOAD_FOLDER"],room_token=room_token)
    print(current_folder)
    breadcrumbs = get_breadcrumbs(current_folder=current_folder)
    form = UploadFileForm()
    room_token = DEFAULT_ROOM_TOKEN
    #Make sure files are not expired
    # uploaded_files:File = db.session.execute(db.select(File).where(File.expires_at > now)
    
    #Gets all the subfolders and files of the current folder
    subfolders, files,rel_paths = get_children(token=token,room_token=room_token,
                                    current_folder=current_folder) 
    
    return render_template("room.html",form=form,subfolders=subfolders,files=files,room_token=room_token,token=token,
                           breadcrumbs=breadcrumbs)

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
            
            storage_dir = os.path.join(app.config["UPLOAD_FOLDER"],room_token,token) #Will be stored in the storage directory with it's associated token
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


@app.route("/download/<room_token>/<token>")
def download(room_token,token):
    """Download desired files/folders"""
    current_folder = request.args.get("current_folder","")
    print(current_folder)
    filename = request.args.get("filename","]omad[fhn[adofihand[hfoindah[oifndhafhniupn]]]]")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip") 
    tmp.close()  
    
    current_folder = sanitize_rel_path(current_folder) 
    
    print(f"Current file: {filename}")
    base_dir = os.path.join(app.config["UPLOAD_FOLDER"], room_token, token)
    current_dir = os.path.join(base_dir,current_folder) #The current folder the user's downloading
    
    print(f"Current Dir: {current_dir}")
    file_path = os.path.join(current_dir, sanitize_rel_path(filename))
    print(f"File Path: {file_path}")
    #Checks if the user's downloading a file
    if os.path.isfile(file_path): 
        print(file_path)
        return send_from_directory(directory=current_dir,path=filename,as_attachment=True,
                                   download_name=filename)
    #Checks if the user's downloading a folder
    elif os.path.isdir(current_dir):
        print(f"Current Dir: {current_dir}")
        #The "root" is the current folder os.walk() is in
        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as archive:
            for root, dirs, files in os.walk(current_dir): #Goes down each level of the directory tree
                for file in files: 
                    abs_path = os.path.join(root,file)
                    rel_path = os.path.relpath(abs_path,start=current_dir) #Rel path based on a starting directory
                    archive.write(abs_path,arcname=rel_path)
                    
        zip_name = os.path.join(os.path.basename(current_dir),".zip")
        return send_file(tmp.name,as_attachment=True,download_name=zip_name, #Takes only the folder name
                            mimetype="application/zip")
    # else:
    #     abort(404)
    #     time.sleep(2)
    #     return redirect(url_for("room",token=token,room_token=room_token))
    
    
    
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