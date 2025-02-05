import os
from datetime import datetime
from flask import Flask, redirect, request, jsonify, session
import requests
import urllib.parse
import json

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
API_BASE_URL = os.getenv("API_BASE_URL")

app = Flask(__name__)
app.secret_key = 'f8Ugh5WbD8DrUZAwzeL5f73TBHf3Knlu'

@app.route('/')
def index():
    return "Welcome to WhatMusicDoILike? <a href='/login'>Login with Spotify</a>"

@app.route('/login')
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

    return redirect(auth_url)

@app.route('/callback')
def callback():
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

        return redirect('/playlists')
    
@app.route('/playlists')
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

    session['playlist_ids'] = playlist_ids

    print(session['playlist_ids'][0])

    return redirect('/modify-playlists')

@app.route('/playlistsitems')
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
    for id in playlist_ids:
        response = requests.get(API_BASE_URL + f'playlists/{id}/tracks', headers=headers)
        tracks = response.json()
        all_tracks.append(tracks)

    return all_tracks

# requires playlistid, tracks to be added
@app.route('/modify-playlists')
def modify_playlists():
    api_playlist = session['playlist_ids'][0]

    request_body = {
        "uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh","spotify:track:1301WleyT98MSxVHPZCA6M"]
    }

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.post(API_BASE_URL + f'playlists/{api_playlist}/tracks', headers=headers, json=request_body)

    if response.status_code == 201:
        return jsonify({'message': 'Tracks added successfully'}), 200
    else:
        return jsonify({'error': response.json()}), response.status_code


@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    

    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)