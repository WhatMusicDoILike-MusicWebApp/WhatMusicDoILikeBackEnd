from app.models.database import db  

class Song(db.Model):  
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    track_title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    
    playlists = db.relationship('PlaylistHas', back_populates='song')
