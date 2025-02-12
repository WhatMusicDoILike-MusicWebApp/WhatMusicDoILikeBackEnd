from flask import Blueprint, jsonify, request
from app.models.database import db

import os
from datetime import datetime
from flask import Flask, redirect, session
import requests
import urllib.parse
import json

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
API_BASE_URL = os.getenv("API_BASE_URL")

spotify_auth_bp = Blueprint('spotify_auth', __name__)

@spotify_auth_bp.route('/spotify/fetchData', methods=['POST'])
def spotify_auth():
    print("Authorizing Spotify Account...")
    
    user_credentials = request.get_json()
    # Log in to spotify
    return login()



# Function to authenticate user with Spotify
def login():
    scope = 'user-read-private user-read-email playlist-read-private playlist-modify-public playlist-modify-private'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("User sent to login\n")
    print(auth_url)
    return redirect(auth_url)

# function to get spotify tokens using code from authentification
@spotify_auth_bp.route('/callback')
def callback():
    print('\ncallback reached\n')
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        print(f"Access token: {session['access_token']}   End")
        print("\n")
        print(f"Refresh token: {session['refresh_token']}   End")

        return get_playlists()
    
    return "Failure"

# get all playlist ids and names
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    playlist_ids = [playlist['id'] for playlist in playlists.get('items', [])]
    playlist_names = [playlist['name'] for playlist in playlists.get('items', [])]

    playlist_map = {}
    for id, names in zip(playlist_ids, playlist_names):
        playlist_map[id] = names

    print(f"Playlist Dict:  {playlist_map}")

    session['playlist_ids'] = playlist_ids

    print("\n\nSUCCESS")
    return get_playlists_items()

# get all tracks from all playlists
def get_playlists_items():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    if 'playlist_ids' not in session:
        return "No playlist IDS found", 400
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    playlist_ids = session['playlist_ids']
    all_tracks = []
    total_tracks = 0
    for id in playlist_ids:
        response = requests.get(API_BASE_URL + f'playlists/{id}/tracks?fields=items(track(name,artists(name)))', headers=headers)
        tracks = response.json()

        track_items = tracks.get('items', [])
        all_tracks.append(track_items)

        total_tracks += len(track_items)

    session['tracks'] = all_tracks

    print(total_tracks)
    return "Success"