from flask import Blueprint, jsonify, request
from app.models.database import db
from app.models import User, Playlist, Song, PlaylistHas
import requests
import base64
from dotenv import load_dotenv
import os
import time

load_dotenv('.env')
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

MAX_RETRIES = 3
RETRY_DELAY = 1

spotify_auth_bp = Blueprint('spotify_auth_bp', __name__)

@spotify_auth_bp.route('/spotify/fetchUserData', methods=['POST'])
def fetch_spotify_user_data():
    """Main function to fetch user's Spotify data following the pseudocode logic"""
    request_data = request.get_json()
    print(request_data)
    
    if 'error' in request_data:
        return jsonify({"error": request_data['error']})
    
    if 'code' not in request_data:
        return jsonify({"error": "No authorization code provided"})
    
    code = request_data['code']
    clerk_unique_id = request_data['userId']
    print(clerk_unique_id)
    
    for attempt in range(MAX_RETRIES):
        try:
            token_info = fetch_auth_token(code)
            print(f"Auth token attempt {attempt + 1}: {token_info}")
            
            if 'error' not in token_info and 'access_token' in token_info:
                break
            
            if attempt < MAX_RETRIES - 1:
                print(f"Auth token fetch failed, retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Auth token fetch exception on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    if 'error' in token_info or 'access_token' not in token_info:
        return jsonify({"error": token_info.get('error', 'Failed to obtain authentication token')})
    
    for attempt in range(MAX_RETRIES):
        try:
            playlists = fetch_playlists(token_info['access_token'])
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
    
    if db_response:
        return jsonify(playlists)
    else:
        return jsonify({"error": "Error storing songs in database after multiple attempts"})

def fetch_auth_token(code):
    """Fetch authentication token from Spotify API"""
    REDIRECT_URI = 'http://localhost:5173/dashboard'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'

    req_body = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }

    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    base64_creds = base64.b64encode(client_creds.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64_creds}'
    }

    try:
        response = requests.post(TOKEN_URL, data=req_body, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def fetch_playlists(token):
    """Fetch all playlists for the user"""
    API_BASE_URL = 'https://api.spotify.com/v1/'

    headers = {
        'Authorization': f"Bearer {token}"
    }

    try:
        response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
        playlists_data = response.json()
        
        if 'error' in playlists_data:
            print(f"Spotify API error: {playlists_data['error']}")
            return []
        
        processed_playlists = []
        
        for playlist in playlists_data.get('items', []):
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            
            songs = []
            for attempt in range(MAX_RETRIES):
                try:
                    songs = fetch_songs(token, playlist_id)
                    if songs:
                        break
                        
                    if attempt < MAX_RETRIES - 1:
                        print(f"Failed to fetch songs for playlist {playlist_name}, retrying...")
                        time.sleep(RETRY_DELAY)
                except Exception as e:
                    print(f"Exception fetching songs for playlist {playlist_name} on attempt {attempt + 1}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
            
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
                    response = requests.get(
                        f"{API_BASE_URL}playlists/{playlist_id}/tracks?offset={offset}&fields=items(track(name,artists(name))),total",
                        headers=headers
                    )
                    
                    tracks_data = response.json()
                    
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