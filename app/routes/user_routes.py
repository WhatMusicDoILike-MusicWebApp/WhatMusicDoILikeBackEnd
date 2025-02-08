from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models.user import User

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['POST'])
def new_user():
    print("User route working!")
    data = request.get_json()  # Get JSON payload from request

    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_user = User(name=name, email=email)
        db.session.add(new_user)  # Add to session
        db.session.commit()  # Commit transaction

        return jsonify({"message": "User created successfully!", "userId": new_user.id}), 201
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500
