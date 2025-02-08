from app.models.database import db  

class Song(db.Model):  
    __tablename__ = 'songs'

    songId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trackName = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    
    playlists = db.relationship('PlaylistHas', back_populates='song')
