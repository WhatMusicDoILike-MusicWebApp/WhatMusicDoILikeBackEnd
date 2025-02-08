from app.models.database import db  

class PlaylistHas(db.Model): 
    __tablename__ = 'playlist_has'

    playlistId = db.Column(db.Integer, db.ForeignKey('playlists.playlistId'), nullable=False, primary_key=True)
    songId = db.Column(db.Integer, db.ForeignKey('songs.songId'), nullable=False, primary_key=True)
    
    playlist = db.relationship('Playlist', back_populates='songs')
    song = db.relationship('Song', back_populates='playlists')

    __table_args__ = (
        db.UniqueConstraint('playlistId', 'songId', name='uix_playlist_song'),
    )

