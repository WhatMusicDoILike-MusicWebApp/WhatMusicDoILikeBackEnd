from app.models.playlist import Playlist
from app.models.playlist_has import PlaylistHas
from app.models.track import Track 
from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models.user import User

playlist_bp = Blueprint('playlist_bp', __name__)

@playlist_bp.route('/playlists', methods=['GET'])
def get_user_playlist():
    user_id = request.args.get('userId') 

    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400

    user = User.query.filter_by(userId=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    playlists = Playlist.query.filter_by(playlistOwnerId=user_id).all()

    playlists_data = []
    for playlist in playlists:
        tracks = (
            db.session.query(Track)
            .join(PlaylistHas, PlaylistHas.trackId == Track.trackId)
            .filter(PlaylistHas.playlistId == playlist.playlistId)
            .all()
        )
        track_data = [{"trackId": track.trackId, "name": track.trackName, "artist": track.artist, "imageUrl": track.imageUrl, "trackUrl": track.trackUrl} for track in tracks]
        playlists_data.append({
            "playlistId": playlist.playlistId,
            "playlistName": playlist.playlistName,
            "playlistUrl": playlist.playlistUrl,
            "tracks": track_data
        })

    return jsonify({
        "userId": user.userId,
        "playlists": playlists_data
    }), 200