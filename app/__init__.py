import atexit
from app.models import PlaylistHas
from app.models.playlist import Playlist
from app.models.song import Song
from app.models.user import User
from flask import Flask
from flask_cors import CORS
from app.models.database import db

def create_app():
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:5173"])


    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://testMusicUser:testMusicPassword@localhost/music_db' #mysql+pymysql://testMusicUser:testMusicPassword@localhost/music_db
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  

    with app.app_context():
        db.drop_all()   # Drop all tables
        db.create_all()  # Create all tables based on your models

        # Dummy data
        dummy_users = [
            User(userId= "1", name="Iker", email="Iker@example.com", spotifyId="sp_123", youtubeId="yt_123", appleMusicId="am_123"),
            User(userId= "2", name="Maayan", email="Maayan@example.com"),
            User(userId= "3", name="Caleb", email="Caleb@example.com:"),
            User(userId= "4", name="Ethan", email="Ethan@exampel.com"),

            Playlist(playlistName="Iker's Playlist", playlistOwnerId=1),
            Playlist(playlistName="Maayan's Playlist", playlistOwnerId=2),
            Playlist(playlistName="Caleb's Playlist", playlistOwnerId=3),
            Playlist(playlistName="Ethan's Playlist", playlistOwnerId=4),

            Song(trackName="Song 1", artist="Artist 1"),
            Song(trackName="Song 2", artist="Artist 2"),
            Song(trackName="Song 3", artist="Artist 3"),
            Song(trackName="Song 4", artist="Artist 4"),

            PlaylistHas(playlistId=1, songId=1),
            PlaylistHas(playlistId=1, songId=2),
            PlaylistHas(playlistId=2, songId=3),
            PlaylistHas(playlistId=2, songId=1),
            PlaylistHas(playlistId=3, songId=4),
            PlaylistHas(playlistId=4, songId=2),
            PlaylistHas(playlistId=4, songId=3)
        ]

        db.session.add_all(dummy_users)
        db.session.commit()  # Save dummy data to the database

    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    def cleanup():
        with app.app_context():
            print("Dropping all tables before shutdown...")
            db.drop_all()

    atexit.register(cleanup)

    return app
