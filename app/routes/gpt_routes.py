import os
from openai import OpenAI
from app.models.playlist import Playlist
from app.models.playlist_has import PlaylistHas
from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models.track import Track
from dotenv import load_dotenv

gpt_bp = Blueprint('gpt_bp', __name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

@gpt_bp.route('/fetchRecommendations', methods=['POST'])
def fetch_recommendations():
    data = request.get_json() 
    user_id = data.get('userId')

    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400
    
    playlists = Playlist.query.filter_by(playlistOwnerId=user_id).all()

    if not playlists:
        return jsonify({"error": "No playlists found for this user"}), 404
    
    track_ids = db.session.query(PlaylistHas.trackId).filter(
        PlaylistHas.playlistId.in_([p.playlistId for p in playlists])
    ).distinct().all()  

    if not track_ids:
        return jsonify({"error": "Songs not found in database"}), 404
    
    tracks = db.session.query(Track.trackName, Track.artist).filter(
        Track.trackId.in_([s[0] for s in track_ids])
    ).all()

    if not tracks:
        return jsonify({"error": "Songs not found in database"}), 404

    song_text = "\n".join([f"{title} by {artist}" for title, artist in tracks])

    prompt = (
        "Based on the following list of songs, suggest 5 new songs that the user might like:\n\n" +
        song_text +
        "\n\nProvide the recommendations in JSON format with fields: 'title' and 'artist'. With the recommendation array being called recommendations."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        recommendations = response.choices[0].message.content
        print(recommendations)
        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@gpt_bp.route('/fetchGenres', methods=['POST'])
def fetch_genres():
    data = request.get_json()  
    user_id = data.get('userId')

    if not user_id:
        return jsonify({"error": "Missing userId parameter"}), 400
    
    playlists = Playlist.query.filter_by(playlistOwnerId=user_id).all()

    if not playlists:
        return jsonify({"error": "No playlists found for this user"}), 404
    
    track_ids = db.session.query(PlaylistHas.trackId).filter(
        PlaylistHas.playlistId.in_([p.playlistId for p in playlists])
    ).distinct().all()  

    if not track_ids:
        return jsonify({"error": "Songs not found in database"}), 404
    
    tracks = db.session.query(Track.trackName, Track.artist).filter(
        Track.trackId.in_([s[0] for s in track_ids])
    ).all()

    if not tracks:
        return jsonify({"error": "Songs not found in database"}), 404

    track_text = "\n".join([f"{title} by {artist}" for title, artist in tracks])

    prompt = (
        "Based on the following list of songs, give me my top 5 genres.\n\n" +
        track_text +
        "\n\nProvide the genres in JSON format with fields: 'genre' and 'explanation'. With the genre array being called topGenres."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        recommendations = response.choices[0].message.content
        print(recommendations)
        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500