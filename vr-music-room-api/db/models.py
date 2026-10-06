import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from db.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    spotify_token = Column(Text, nullable=True)
    spotify_refresh = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PreloadedAsset(Base):
    __tablename__ = "preloaded_assets"

    id = Column(String, primary_key=True, default=gen_uuid)
    asset_type = Column(String, nullable=False)  # "skybox" or "texture"
    tags = Column(Text, nullable=False)           # JSON array string
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    id = Column(String, primary_key=True, default=gen_uuid)
    spotify_track_id = Column(String, nullable=True)
    asset_type = Column(String, nullable=False)
    prompt_used = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    mood_tags = Column(Text, nullable=True)       # JSON array string
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    favorite_vibes = Column(Text, nullable=True)  # JSON array string
    texture_quality = Column(String, default="medium")