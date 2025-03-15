from app.models.database import db  

class Track(db.Model):  
    __tablename__ = 'tracks'

    trackId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trackName = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    imageUrl = db.Column(db.String(255), nullable=True)
    
    playlists = db.relationship('PlaylistHas', back_populates='track')