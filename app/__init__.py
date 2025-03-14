import atexit
from app.models import PlaylistHas
from app.models.playlist import Playlist
from app.models.song import Song
from app.models.user import User
from flask import Flask
from flask_cors import CORS
from app.models.database import db
import os

def create_app(config_name=None):
    app = Flask(__name__)

    CORS(app, origins=["http://localhost:5173"])

    if config_name == "testing":
        # Use SQLite for testing or in-memory database 
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:

        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql+pymysql://test_user:test_password@localhost/test_backend')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Setup dummy data only for non-testing environment
    if config_name != "testing":
        with app.app_context():
            db.create_all()  

            dummy_users = [
                User(userId="1", name="Iker", email="Iker@example.com"),
                User(userId="2", name="Maayan", email="Maayan@example.com"),
                User(userId="3", name="Caleb", email="Caleb@example.com"),
                User(userId="4", name="Ethan", email="Ethan@example.com"),
                User(userId="user_2trNFZ2SND2DwViOf1fS5PCkvQf", name="Maayan Israel", email="datcubingkid@gmail.com"),

                Playlist(playlistName="Iker's Playlist", playlistOwnerId=1),
                Playlist(playlistName="Maayan's Playlist", playlistOwnerId=2),
                Playlist(playlistName="Caleb's Playlist", playlistOwnerId=3),
                Playlist(playlistName="Ethan's Playlist", playlistOwnerId=4),

                Song(trackName="Billie Jean", artist="Michael Jackson"),
                Song(trackName="Stayin' Alive", artist="Bee Gees"),
                Song(trackName="Song 3", artist="Artist 3"),
                Song(trackName="Song 4", artist="Artist 4"),
                Song(trackName="You'll Never Walk Alone", artist="Gerry & The Pacemakers"),
                Song(trackName="Hey Jude", artist="The Beatles"),
                Song(trackName="Sunflower", artist="Post Malone, Swae Lee"),

                PlaylistHas(playlistId=1, songId=1),
                PlaylistHas(playlistId=1, songId=2),
                PlaylistHas(playlistId=1, songId=5),
                PlaylistHas(playlistId=1, songId=6),
                PlaylistHas(playlistId=1, songId=7),

                PlaylistHas(playlistId=2, songId=3),
                PlaylistHas(playlistId=2, songId=1),
                PlaylistHas(playlistId=3, songId=4),
                PlaylistHas(playlistId=4, songId=2),
                PlaylistHas(playlistId=4, songId=3)
            ]

            db.session.add_all(dummy_users)
            db.session.commit()

    from app.routes import user_bp, gpt_bp, spotify_auth_bp
    app.register_blueprint(gpt_bp)
    app.register_blueprint(spotify_auth_bp)
    app.register_blueprint(user_bp)

    def cleanup():
        with app.app_context():
            print("Dropping all tables before shutdown...")
            db.drop_all()

    atexit.register(cleanup)

    return app
