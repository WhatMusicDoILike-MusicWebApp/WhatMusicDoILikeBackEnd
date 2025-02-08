from app.models.database import db

class Playlist(db.Model):  
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user = db.relationship('User', back_populates='playlists')
    songs = db.relationship('PlaylistHas', back_populates='playlist')
