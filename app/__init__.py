from flask import Flask
from app.models.database import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:777@localhost/postgres'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  

    with app.app_context():
        db.drop_all()   # Drop all tables
        db.create_all()  # Create all tables based on your models

    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    return app
