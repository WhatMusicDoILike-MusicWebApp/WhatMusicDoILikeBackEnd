from sqlalchemy import JSON
from app.models.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    userId = db.Column(db.String(255), primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    spotifyId = db.Column(db.String(255), unique=True, nullable=True)
    youtubeId = db.Column(JSON, nullable=True)
    appleMusicId = db.Column(db.String(255), unique=True, nullable=True)
    spotifyAuthToken = db.Column(db.String(319), nullable=True)
    spotifyRefreshToken = db.Column(db.String(319), nullable=True)
    
    playlists = db.relationship('Playlist', back_populates='user')
