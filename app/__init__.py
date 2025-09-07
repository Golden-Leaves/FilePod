import os
from datetime import timedelta
from flask import Flask
from flask_session import Session
from flask_bootstrap5 import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from .blueprints.rooms import bp as rooms_bp
from .blueprints.room import bp as room_bp
from .blueprints.transfers import bp as transfers_bp
from .helpers.general import format_file_size
from .models import File,db

bootstrap = Bootstrap()
session_ext = Session()

DEFAULT_ROOM_TOKEN = "default_room"
DEFAULT_TTL = timedelta(hours=1)

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    instance_path = os.path.join(project_root,"instance") 
    load_dotenv(os.path.join(os.path.dirname(base_dir), ".env"), override=True)

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
        instance_path=instance_path
    )
    os.makedirs(app.instance_path, exist_ok=True)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SESSION_TYPE"] = "filesystem"
    db_path = os.path.join(app.instance_path, "files.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.replace("\\", "/")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "storage")

    bootstrap.init_app(app)
    session_ext.init_app(app)
    db.init_app(app)

    
    app.jinja_env.filters["format_filesize"] = format_file_size
    from . import models
    @app.cli.command()
    def createdb():
        from . import db, models
        with app.app_context():
            db.create_all()
            print("created tables:", [t.name for t in db.metadata.sorted_tables])
            print("instance_path:", app.instance_path) #Fuck you instance path
            print("db_uri:", app.config["SQLALCHEMY_DATABASE_URI"])
            
    os.makedirs(app.config["UPLOAD_FOLDER"],exist_ok=True)


    app.register_blueprint(rooms_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(transfers_bp)

    app.config["DEFAULT_ROOM_TOKEN"] = DEFAULT_ROOM_TOKEN
    app.config["DEFAULT_TTL"] = DEFAULT_TTL

    return app