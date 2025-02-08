from flask import Blueprint, request, jsonify
from app.models import Playlist  # Import your Playlist model

playlist_bp = Blueprint("playlist", __name__)

@playlist_bp.route('/playlists', methods=['GET'])
def get_playlists():
    # Query the Playlist model for all playlists
    playlists = Playlist.query.all()
    
    # Convert the playlists to a list of dictionaries for the response
    playlists_list = [{"id": playlist.id, "name": playlist.name} for playlist in playlists]
    
    return jsonify(playlists_list)

