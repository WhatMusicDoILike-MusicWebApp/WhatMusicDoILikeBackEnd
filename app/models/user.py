from app.models.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    spotifyId = db.Column(db.String(255), unique=True, nullable=True)
    youtubeId = db.Column(db.String(255), unique=True, nullable=True)
    appleMusicId = db.Column(db.String(255), unique=True, nullable=True)
    
    playlists = db.relationship('Playlist', back_populates='user')
