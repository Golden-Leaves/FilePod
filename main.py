from datetime import datetime,timezone,timedelta
from flask import Flask, abort, render_template, redirect, url_for, flash,session,request,jsonify,Blueprint
from flask_session import Session
from flask_bootstrap5 import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import secrets
from werkzeug.utils import secure_filename

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),".env")
load_dotenv(env_path)
DEFAULT_TTL = timedelta(hours=1)
app = Flask(__name__,static_folder="static",template_folder="templates")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"

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
    name: Mapped[str] = mapped_column(String(255)) #File/Folder name
    stored_path: Mapped[str] = mapped_column(Text)
    size: Mapped[int] = mapped_column(Integer) #Size in bytes
    mime: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc) + DEFAULT_TTL)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0) #How many times it has been downloaded
    
with app.app_context():
    db.create_all()
    os.makedirs(os.path.join(app.root_path, "storage"), exist_ok=True)
    
@app.route("/room",methods=["GET","POST"])
def room():
    return render_template("room.html")

@app.route("/upload",methods=["POST"])
def upload():#Uploads the file to a storage folder and saves metadata to db
    files = request.files.getlist("files") #FileStorage type
    uploaded = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token = secrets.token_urlsafe(16) #Some random token
    for f in files:
        filename = secure_filename(f.filename)
        print(filename)
        storage_dir = os.path.join(base_dir,"storage",token) #Will be stored in the storage directory with it's associated token
        os.makedirs(storage_dir,exist_ok=True)
        stored_path = os.path.join(storage_dir,filename)
        f.save(stored_path) #Saves the file/folder uploaded into the storage path
        
        file = File()
        file.token = token
        file.name = f.filename
        file.stored_path = stored_path
        file.size = os.path.getsize(stored_path) #Get filesize(in bytes)
        file.mime = f.mimetype
        file.expires_at = datetime.now(timezone.utc) + DEFAULT_TTL #default TTL for now
        db.session.add(file)
        db.session.commit()
        
        uploaded.append({
            "token": token,
            "name": f.filename,
            "size": os.path.getsize(stored_path),
            "expires_at": (datetime.now(timezone.utc) + DEFAULT_TTL).isoformat() + "Z",
            "downloads": 0
        })
        
    return jsonify({"uploaded":uploaded})
@app.route("/files")
def files(): 
    """Returns a JSON of File objects"""
    now = datetime.now(timezone.utc)
    rows = db.session.execute(db.select(File).where(File.expires_at > now)).scalars().all()
    payload = []
    for row in rows:
       payload.append({
            "token": row.token,
            "name": row.name,
            "size": row.size,
            "mime": row.mime,
            "expires_at": row.expires_at.isoformat(),
            "download_count": row.download_count,
        })
    return jsonify(payload)
if __name__ == "__main__":
    app.run(debug=True)