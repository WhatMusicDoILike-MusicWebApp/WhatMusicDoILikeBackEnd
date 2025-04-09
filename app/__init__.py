import atexit
from app.models import PlaylistHas
from app.models.playlist import Playlist
from app.models.track import Track
from app.models.user import User
from flask import Flask
from flask_cors import CORS
from app.models.database import db
import os
from dotenv import load_dotenv


load_dotenv()


def create_app():
    app = Flask(__name__)
    
    load_dotenv('.env')
    dev_mode = os.environ.get('DEVELOPEMENT_MODE')


    if dev_mode == 'True':
        CORS(app, origins=['http://localhost:5173'])
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://testMusicUser:testMusicPassword@localhost/music_db'
    else:
        main_branch = 'https://www.whatmusicdoilike.com'
        dev_branch = 'https://www.dev.whatmusicdoilike.com'
        CORS(app, origins=[main_branch, dev_branch])

        db_user = os.environ.get('DB_USERNAME')
        db_password = os.environ.get('DB_PASSWORD')
        db_endpoint = os.environ.get('DB_ENDPOINT')
        db_name = 'music_db'

        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_endpoint}/{db_name}'

    db.init_app(app)  

    with app.app_context():
        db.drop_all()   
        db.create_all()  

        dummy_data = [
            User(userId= "1", name="Iker", email="Iker@example.com"),
            Playlist(playlistName="Iker's Playlist", playlistOwnerId=1, playlistUrl="https://google.com"),
            Track(trackName="Billie Jean", artist="Michael Jackson", trackUrl="https://google.com"),
            PlaylistHas(playlistId=1, trackId=1),

            User(userId= "2", name="Yu Sun", email="YuSun@example.com"),
        ]

        db.session.add_all(dummy_data)
        db.session.commit()  

    from app.routes import user_bp, gpt_bp, spotify_auth_bp, youtube_auth_bp, playlist_bp
    app.register_blueprint(gpt_bp)
    app.register_blueprint(spotify_auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(youtube_auth_bp)
    app.register_blueprint(playlist_bp)

    def cleanup():
        with app.app_context():
            print("Dropping all tables before shutdown...")
            db.drop_all()

    atexit.register(cleanup)

    return app