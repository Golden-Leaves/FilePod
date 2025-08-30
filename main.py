from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash,session
from flask_session import Session
from flask_bootstrap5 import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)
def 