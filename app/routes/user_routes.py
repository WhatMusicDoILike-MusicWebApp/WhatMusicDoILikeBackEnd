from app.models.playlist import Playlist
from app.models.playlist_has import PlaylistHas
from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models.user import User

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['POST'])
def new_user():
    print("User route working!")
    data = request.get_json()  # Get JSON payload from request

    user_id = data.get('userId')
    name = data.get('name')
    email = data.get('email')
    spotify_id = data.get('spotifyId', "")  # Provide default value
    youtube_id = data.get('youtubeId', "")
    apple_music_id = data.get('appleMusicId', "")

    if not user_id or not name or not email:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_user = User(userId=user_id, name=name, email=email, spotifyId=spotify_id, youtubeId=youtube_id, appleMusicId=apple_music_id)
        db.session.add(new_user)  # Add to session
        db.session.commit()  # Commit transaction

        return jsonify({"message": "User created successfully!", "userId": new_user.userId}), 201
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500
    
@user_bp.route('/users', methods=['GET'])
def get_user():
    user_id = request.args.get('userId')  # Get userId from query params

    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400

    user = User.query.filter_by(userId=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "userId": user.userId,
        "name": user.name,
        "email": user.email
    }), 200

@user_bp.route('/users', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('userId')  # Get userId from query parameters

    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400

    user = User.query.filter_by(userId=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Fetch all playlist IDs owned by the user
        playlists = Playlist.query.filter_by(playlistOwnerId=user_id).all()
        playlist_ids = [playlist.playlistId for playlist in playlists]

        if playlist_ids:
            # Delete all PlaylistHas entries related to the playlists
            PlaylistHas.query.filter(PlaylistHas.playlistId.in_(playlist_ids)).delete(synchronize_session=False)

            # Delete all Playlists owned by the user
            Playlist.query.filter(Playlist.playlistId.in_(playlist_ids)).delete(synchronize_session=False)

        # Delete user from Users table
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User Successfully Deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_bp.route('/users', methods=['PUT'])
def update_user():
    data = request.get_json()  # Get JSON payload from request
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