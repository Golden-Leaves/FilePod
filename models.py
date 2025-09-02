from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,ForeignKey
from datetime import datetime,timezone,timedelta
class Base(DeclarativeBase):
    pass

DEFAULT_TTL = timedelta(hours=1)
db = SQLAlchemy(model_class=Base)
DEFAULT_TTL = 60
class File(db.Model):
    """A class to handle files"""
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(32),index=True,nullable=False) #Unique Token Identifier(imagine duplicates + security)
    name: Mapped[str] = mapped_column(String(255)) #File/Folder name, can also act as relative path
    stored_path: Mapped[str] = mapped_column(Text) #The FULL path to the file
    size: Mapped[int] = mapped_column(Integer) #Size in bytes
    mime: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(128)) #The simplified "type" derived from mime: "Images","Documents",...
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc) + DEFAULT_TTL)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0) #How many times it has been downloaded
    rel_path: Mapped[str] = mapped_column(Text) #Saves the FULL relative path of the file(including all parents)
    parent_folder: Mapped[str] = mapped_column(Text) #Only saves the parents