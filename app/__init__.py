import atexit
from app.models import PlaylistHas
from app.models.playlist import Playlist
from app.models.track import Track
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
        db.drop_all()   
        db.create_all()  

        dummy_users = [
            User(userId= "1", name="Iker", email="Iker@example.com"),
            User(userId= "2", name="Maayan", email="Maayan@example.com"),
            User(userId= "3", name="Caleb", email="Caleb@example.com:"),
            User(userId= "4", name="Ethan", email="Ethan@exampel.com"),
            User(userId= "user_2trNFZ2SND2DwViOf1fS5PCkvQf", name="Maayan Israel", email="datcubingkid@gmail.com", ),

            Playlist(playlistName="Iker's Playlist", playlistOwnerId=1),
            Playlist(playlistName="Maayan's Playlist", playlistOwnerId=2),
            Playlist(playlistName="Caleb's Playlist", playlistOwnerId=3),
            Playlist(playlistName="Ethan's Playlist", playlistOwnerId=4),

            Track(trackName="Billie Jean", artist="Michael Jackson"),
            Track(trackName="Stayin' Alive", artist="Bee Gees"),
            Track(trackName="Track 3", artist="Artist 3"),
            Track(trackName="Track 4", artist="Artist 4"),
            Track(trackName="You'll Never Walk Alone", artist="Gerry & The Pacemakers"),
            Track(trackName="Hey Jude", artist="The Beatles"),
            Track(trackName="Sunflower", artist="Post Malone, Swae Lee"),


            PlaylistHas(playlistId=1, trackId=1),
            PlaylistHas(playlistId=1, trackId=2),
            PlaylistHas(playlistId=1, trackId=5),
            PlaylistHas(playlistId=1, trackId=6),
            PlaylistHas(playlistId=1, trackId=7),

            PlaylistHas(playlistId=2, trackId=3),
            PlaylistHas(playlistId=2, trackId=1),
            PlaylistHas(playlistId=3, trackId=4),
            PlaylistHas(playlistId=4, trackId=2),
            PlaylistHas(playlistId=4, trackId=3)
        ]

        db.session.add_all(dummy_users)
        db.session.commit()  

    from app.routes import user_bp, gpt_bp, spotify_auth_bp, playlist_bp
    app.register_blueprint(gpt_bp)
    app.register_blueprint(spotify_auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(playlist_bp)

    def cleanup():
        with app.app_context():
            print("Dropping all tables before shutdown...")
            db.drop_all()

    atexit.register(cleanup)

    return app
