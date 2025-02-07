from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    
    playlists = relationship('Playlist', back_populates='user')

class Playlist(Base):
    __tablename__ = 'playlists'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    user = relationship('User', back_populates='playlists')
    songs = relationship('PlaylistSong', back_populates='playlist')

class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    track_title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    
    playlists = relationship('PlaylistSong', back_populates='song')

class PlaylistSong(Base):
    __tablename__ = 'playlist_songs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('playlists.id'), nullable=False)
    song_id = Column(Integer, ForeignKey('songs.id'), nullable=False)
    
    playlist = relationship('Playlist', back_populates='songs')
    song = relationship('Song', back_populates='playlists')
