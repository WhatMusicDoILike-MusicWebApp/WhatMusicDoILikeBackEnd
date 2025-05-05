from app.models.database import db

class Playlist(db.Model):  
    __tablename__ = 'playlists'
    
    playlistId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    playlistName = db.Column(db.String(255), nullable=False)
    playlistUrl = db.Column(db.String(255), nullable=False)
    playlistImageUrl = db.Column(db.String(255), nullable=True)
    playlistOwnerId = db.Column(db.String(255), db.ForeignKey('users.userId'), nullable=False)
    isYt = db.Column(db.Boolean)
    
    user = db.relationship('User', back_populates='playlists')
    tracks = db.relationship('PlaylistHas', back_populates='playlist')
