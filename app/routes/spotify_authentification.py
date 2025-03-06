from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models import User, Playlist, Song, PlaylistHas
import requests
import base64
from dotenv import load_dotenv
import os
import time
from urllib.parse import urlencode

load_dotenv('.env')
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

MAX_RETRIES = 3
RETRY_DELAY = 1

spotify_auth_bp = Blueprint('spotify_auth_bp', __name__)

@spotify_auth_bp.route('/spotify/initializeConnection', methods=['POST'])
def initialize_spotify_connection():
    """Initializes the Spotify connection for the user"""
    request_data = request.get_json()
    print(request_data)

    if 'code' not in request_data:
        return jsonify({"error": "No authorization code provided"})
    
    if 'userId' not in request_data:
        return jsonify({"error": "No user ID provided"})
    
    user_id = request_data['userId']
    
    user = User.query.filter_by(userId=user_id).first()
    if not user:
        return jsonify({"error": "User not found"})
    
    if user.spotifyAuthToken:
        return jsonify({"error": "User already has a Spotify connection"})
    
    REDIRECT_URI = 'http://localhost:5173/dashboard'
    AUTH_URL = 'https://accounts.spotify.com/api/token'
    
    query_params = {
        'grant_type': 'authorization_code',
        'code': request_data['code'],
        'redirect_uri': REDIRECT_URI,
    }

    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    base64_creds = base64.b64encode(client_creds.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64_creds}'
    }
    
    try:
        response = requests.post(AUTH_URL, params=query_params, headers=headers)
        if 'error' in response.json() or 'access_token' not in response.json():
            return jsonify({"error": response.json()['error']})
        user.spotifyAuthToken = response.json().get('access_token')
        user.spotifyRefreshToken = response.json().get('refresh_token')
        db.session.commit()
        return jsonify({
            "message": "Succesfuly connected spotify!",
            "userId": user.userId,
            "spotifyAuthToken": user.spotifyAuthToken,
            "spotifyRefreshToken": user.spotifyRefreshToken,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)})

@spotify_auth_bp.route('/spotify/fetchUserData', methods=['GET'])
def fetch_spotify_user_data():
    """Main function to fetch user's Spotify data following the pseudocode logic"""
    request_data = request.get_json()
    print(request_data)
    
    if 'error' in request_data:
        return jsonify({"error": request_data['error']})
    
    if 'userId' not in request_data:
        return jsonify({"error": "No user ID provided"})
    
    clerk_unique_id = request_data['userId']
    print(clerk_unique_id)

    user = User.query.filter_by(userId=clerk_unique_id).first()
    if not user:
        return jsonify({"error": "User not found"})
    
    if not user.spotifyAuthToken:
        return jsonify({"error": "User does not have a Spotify connection"})
    
    for attempt in range(MAX_RETRIES):
        try:
            playlists = fetch_playlists(user.userId)
            print(f"Playlists fetch attempt {attempt + 1}, got {len(playlists)} playlists")
            
            if playlists:
                break
                
            if attempt < MAX_RETRIES - 1:
                print(f"Playlists fetch failed, retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Playlists fetch exception on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            if attempt == MAX_RETRIES - 1:
                return jsonify({"error": "Failed to fetch playlists after multiple attempts"})
    
    if not playlists:
        return jsonify({"error": "Failed to fetch playlists after multiple attempts"})
    
    for attempt in range(MAX_RETRIES):
        try:
            db_response = store_spotify_songs_in_database(playlists, clerk_unique_id)
            if db_response:
                break
                
            if attempt < MAX_RETRIES - 1:
                print(f"Database storage failed, retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Database storage exception on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            if attempt == MAX_RETRIES - 1:
                return jsonify({"error": "Failed to store songs in database after multiple attempts"})
    
    if db_response:
        return jsonify({
            "userId": clerk_unique_id,
            "playlists": [{"playlistName": playlist['name'], "tracks": playlist['songs']} for playlist in playlists]
        })
    else:
        return jsonify({"error": "Error storing songs in database after multiple attempts"})
    

def refresh_spotify_token(user_id):
    """Refresh the user's Spotify token"""
    user = User.query.filter_by(userId=user_id).first()
    if not user:
        return False
    
    query_params = {
        'grant_type': 'refresh_token',
        'refresh_token': user.spotifyRefreshToken
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    try:
        AUTH_URL = 'https://accounts.spotify.com/api/token'

        response = requests.post(AUTH_URL, params=query_params, headers=headers)

        if 'error' in response.json() or 'access_token' not in response.json():
            print(f"Error refreshing token: {response.json()}")
            raise Exception("Error refreshing token")

        user.spotifyAuthToken = response.json().get('access_token')
        user.spotifyRefreshToken = response.json().get('refresh_token')
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"refresh token error: {e}")
        return False
    
    

def fetch_playlists(user_id):
    """Fetch all playlists for the user"""
    API_BASE_URL = 'https://api.spotify.com/v1/me/playlists'

    token = User.query.filter_by(userId=user_id).first().spotifyAuthToken

    headers = {
        'Authorization': f"Bearer {token}"
    }

    try:
        response = requests.get(API_BASE_URL, headers=headers)
        playlists_data = response.json()
        
        if 'error' in playlists_data:
            print(f"Spotify API error: {playlists_data['error']}")
            refresh_spotify_token(user_id)
            raise Exception("updating auth token and retrying...")
        
        processed_playlists = []
        
        for playlist in playlists_data.get('items', []):
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            
            songs = []
            for attempt in range(MAX_RETRIES):
                try:
                    songs = fetch_songs(token, playlist_id)

                    if 'lengthOfPlaylist' in songs:
                        print(f"Skipping empty playlist {playlist_name}")
                        break

                    if songs:
                        break
                        
                    if attempt < MAX_RETRIES - 1:
                        print(f"Failed to fetch songs for playlist {playlist_name}, retrying...")
                        time.sleep(RETRY_DELAY)
                except Exception as e:
                    print(f"Exception fetching songs for playlist {playlist_name} on attempt {attempt + 1}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
            
            if 'lengthOfPlaylist' not in songs:
                processed_playlists.append({
                    'id': playlist_id,
                    'name': playlist_name,
                    'size': len(songs),
                    'songs': songs
                })
            
        return processed_playlists
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return []

def fetch_songs(token, playlist_id):
    """Fetch all songs from a specific playlist"""
    API_BASE_URL = 'https://api.spotify.com/v1/'

    headers = {
        'Authorization': f"Bearer {token}"
    }
    
    all_tracks = []
    offset = 0
    
    try:
        while True:
            track_items = []
            for attempt in range(MAX_RETRIES):
                try:
                    query_params = {
                        'offset': offset,
                        'fields': 'items(track(name,artists(name))),total'
                    }
                    response = requests.get(
                        f"{API_BASE_URL}playlists/{playlist_id}/tracks",
                        headers=headers,
                        params=query_params
                    )
                    
                    tracks_data = response.json()
                    if 'total' in tracks_data and tracks_data['total'] == 0:
                        return {"lengthOfPlaylist": 0}
                    
                    if 'error' in tracks_data:
                        print(f"Spotify API error fetching tracks: {tracks_data['error']}")
                        if attempt < MAX_RETRIES - 1:
                            print(f"Retrying in {RETRY_DELAY} seconds...")
                            time.sleep(RETRY_DELAY)
                            continue
                    
                    track_items = tracks_data.get('items', [])
                    break
                except Exception as e:
                    print(f"Exception fetching tracks at offset {offset} on attempt {attempt + 1}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
            
            if not track_items:
                break
                
            for track_info in track_items:
                if 'track' in track_info and track_info['track']:
                    track = track_info['track']
                    track_name = track['name']
                    artists = [artist['name'] for artist in track['artists']]
                    
                    all_tracks.append({
                        'name': track_name,
                        'artists': artists,
                        'artist_string': ', '.join(artists)
                    })
            
            offset += 100
            
            if len(track_items) < 100:
                break
                
        return all_tracks
    except Exception as e:
        print(f"Error fetching songs for playlist {playlist_id}: {e}")
        return []

def store_spotify_songs_in_database(playlists, user_id):
    """Store all playlists and songs in the database"""
    try:
        print(f"Storing {len(playlists)} playlists for user {user_id}")

        user = User.query.filter_by(userId=user_id).first()
        if not user:
            print(f"User with ID {user_id} does not exist")
            return False
        
        for playlist in playlists:
            new_playlist = Playlist(
                playlistName=playlist['name'],
                playlistOwnerId=user_id
            )
            
            db.session.add(new_playlist)
            db.session.flush()  # Get the ID without committing
            
            playlist_id = new_playlist.playlistId
            
            for song in playlist['songs']:
                existing_song = Song.query.filter_by(
                    trackName=song['name'],
                    artist=song['artist_string']
                ).first()
                
                if existing_song:
                    song_id = existing_song.songId
                else:
                    new_song = Song(
                        trackName=song['name'],
                        artist=song['artist_string']
                    )
                    db.session.add(new_song)
                    db.session.flush()  # Get the ID without committing
                    song_id = new_song.songId
                
                exists = PlaylistHas.query.filter_by(
                    playlistId=playlist_id, 
                    songId=song_id
                ).first()
                
                if not exists:
                    playlist_has = PlaylistHas(
                        playlistId=playlist_id, 
                        songId=song_id
                    )
                    db.session.add(playlist_has)
            
        db.session.commit()
        return True
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return False