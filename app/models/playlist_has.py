from app.models.database import db  

class PlaylistHas(db.Model): 
    __tablename__ = 'playlist_has'

    playlistId = db.Column(db.Integer, db.ForeignKey('playlists.playlistId'), nullable=False, primary_key=True)
    trackId = db.Column(db.Integer, db.ForeignKey('tracks.trackId'), nullable=False, primary_key=True)
    
    playlist = db.relationship('Playlist', back_populates='tracks')
    track = db.relationship('Track', back_populates='playlists')

    __table_args__ = (
        db.UniqueConstraint('playlistId', 'trackId', name='uix_playlist_track'),
    )

