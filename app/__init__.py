from flask import Flask
from app.models.database import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://testMusicUser:testMusicPassword@localhost/music_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  

    with app.app_context():
        db.create_all()  

    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    from app.routes.playlist_routes import playlist_bp
    app.register_blueprint(playlist_bp)

    return app
