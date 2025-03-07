from app.models.playlist import Playlist
from app.models.playlist_has import PlaylistHas
from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models.user import User
from dotenv import load_dotenv

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['POST'])
def new_user():
    print("User route working!")
    data = request.get_json()  

    user_id = data.get('userId')
    name = data.get('name')
    email = data.get('email')

    if not user_id or not name or not email:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_user = User(userId=user_id, name=name, email=email, spotifyAuthToken='', spotifyRefreshToken='')
        db.session.add(new_user)  
        db.session.commit()  

        return jsonify({"message": "User created successfully!", "userId": new_user.userId}), 201
    except Exception as e:
        db.session.rollback()  
        return jsonify({"error": str(e)}), 500
    
@user_bp.route('/users', methods=['GET'])
def get_user():
    user_id = request.args.get('userId') 

    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400

    user = User.query.filter_by(userId=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "userId": user.userId,
        "name": user.name,
        "email": user.email,
        "spotifyAuthToken": user.spotifyAuthToken,
        "spotifyRefreshToken": user.spotifyRefreshToken
    }), 200

@user_bp.route('/users', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('userId')  
    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400

    user = User.query.filter_by(userId=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        playlists = Playlist.query.filter_by(playlistOwnerId=user_id).all()
        playlist_ids = [playlist.playlistId for playlist in playlists]

        if playlist_ids:
            PlaylistHas.query.filter(PlaylistHas.playlistId.in_(playlist_ids)).delete(synchronize_session=False)

            Playlist.query.filter(Playlist.playlistId.in_(playlist_ids)).delete(synchronize_session=False)

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User Successfully Deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_bp.route('/users', methods=['PUT'])
def update_user():
    data = request.get_json() 
    user_id = data.get('userId')
    new_name = data.get('newName')

    if not user_id or not new_name:
        return jsonify({"error": "Missing userId or newName parameter"}), 400

    user = User.query.filter_by(userId=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        user.name = new_name
        db.session.commit()
        return jsonify({
            "message": "User updated successfully!",
            "userId": user.userId,
            "name": user.name,
            "email": user.email
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500