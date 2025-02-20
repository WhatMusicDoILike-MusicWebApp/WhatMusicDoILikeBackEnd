from app.models.database import db

class Playlist(db.Model):  
    __tablename__ = 'playlists'
    
    playlistId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    playlistName = db.Column(db.String(255), nullable=False)
    playlistOwnerId = db.Column(db.String(255), db.ForeignKey('users.userId'), nullable=False)
    
    user = db.relationship('User', back_populates='playlists')
    songs = db.relationship('PlaylistHas', back_populates='playlist')
