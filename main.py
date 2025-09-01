from datetime import datetime,timezone,timedelta
from flask import (Flask, abort, render_template, redirect, url_for, flash,
                   session,request,jsonify,Blueprint,send_from_directory)
from flask_session import Session
from flask_bootstrap5 import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,ForeignKey
from functools import wraps
import zipfile,os
from dotenv import load_dotenv
import secrets
from werkzeug.utils import secure_filename
from helpers.mime_categorizer import categorize_file
from helpers.general import format_file_size
from forms import UploadFileForm
import tempfile

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),".env")
load_dotenv(env_path)
DEFAULT_TTL = timedelta(hours=1)
app = Flask(__name__,static_folder="static",template_folder="templates")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "storage")
app.jinja_env.filters["format_filesize"] = format_file_size #Sets a sort of function that jinja can use
Bootstrap(app)
Session(app)

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "login"
# @login_manager.user_loader
# def user_loader(user_id):
#     return db.session.execute(db.select(User).where(User.id == user_id)).scalar()
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class File(db.Model):
    """Some Test Docstring"""
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(32), unique=True, index=True) #Unique Token Identifier(imagine duplicates + security)
    name: Mapped[str] = mapped_column(String(255)) #File/Folder name, can also act as relative path
    stored_path: Mapped[str] = mapped_column(Text) #The FULL path to the file
    size: Mapped[int] = mapped_column(Integer) #Size in bytes
    mime: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(128)) #The simplified "type" derived from mime: "Images","Documents",...
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc) + DEFAULT_TTL)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0) #How many times it has been downloaded
    
with app.app_context():
    db.create_all()
    os.makedirs(os.path.join(app.root_path, "storage"), exist_ok=True)
    
@app.route("/room",methods=["GET","POST"])
def room():
    form = UploadFileForm()
    now = datetime.now(timezone.utc)
    #Make sure files are not expired
    uploaded_files:File = db.session.execute(db.select(File).where(File.expires_at > now)).scalars().all()
    return render_template("room.html",form=form,uploaded_files=uploaded_files)

@app.route("/upload",methods=["POST"])
def upload():#Uploads the file to a storage folder and saves metadata to db
    form = UploadFileForm()
    if form.validate_on_submit():
        files = request.files.getlist("files") #If the user uploads multiple files
        print(files)
        token = secrets.token_urlsafe(16) #Some random token
        
        for f in files:
            if not f:
                flash("No file was selected")
            filename = secure_filename(f.filename)
            print(filename)
            storage_dir = os.path.join(app.config["UPLOAD_FOLDER"],token) #Will be stored in the storage directory with it's associated token
            os.makedirs(storage_dir,exist_ok=True)
            stored_path = os.path.join(storage_dir,filename)
            f.save(stored_path) #Saves the file/folder uploaded into the storage path

            file = File()
            file.token = token
            file.name = f.filename
            file.stored_path = stored_path
            file.size = os.path.getsize(stored_path) #File size in Bytes
            file.mime = f.mimetype
            file.type = categorize_file(file_path=stored_path) #Simplified file type
            file.expires_at = datetime.now(timezone.utc) + DEFAULT_TTL #default TTL for now
            db.session.add(file)
        db.session.commit()
        
    return redirect(url_for("room"))

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


@app.route("/download/<token>/<path:filename>")
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
    else:
        return send_from_directory(directory=storage_dir,path=filename,as_attachment=True,
                                   download_name=filename)
    return "Nothing yet baby"
if __name__ == "__main__":
    app.run(debug=True)