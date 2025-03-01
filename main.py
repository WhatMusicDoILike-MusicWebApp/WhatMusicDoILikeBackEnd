import os
from datetime import datetime
from flask import Flask, json, redirect, request, jsonify, session
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from ytmusicapi import OAuthCredentials, YTMusic, setup_oauth
from ytmusicapi.auth.oauth.credentials import Credentials
from ytmusicapi.auth.oauth.token import RefreshingToken
import webbrowser
from typing import Optional
from pathlib import Path



CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
YT_CLIENT_ID = os.getenv("YT_CLIENT")
YT_SECRET = os.getenv("YT_SECRET")

AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
API_BASE_URL = os.getenv("API_BASE_URL")


def patched_prompt_for_token(               #patched ytmusic oauth method for automated authnetication 
    cls, credentials: Credentials, open_browser: bool = False, to_file: Optional[str] = None
) -> "RefreshingToken":
    """
    Method for CLI token creation via user inputs.

    :param credentials: Client credentials
    :param open_browser: Optional. Open browser to OAuth consent url automatically. (Default: ``False``).
    :param to_file: Optional. Path to store/sync json version of resulting token. (Default: ``None``).
    """

    code = credentials.get_code()   
    url = f"{code['verification_url']}?user_code={code['user_code']}"
    if open_browser:
        webbrowser.open(url)

    print(f"Go to {url}, finish the login flow. Waiting for authentication...")

    while True:
        try:
            raw_token = credentials.token_from_code(code["device_code"])
            if raw_token:  # Authentication successful
                ref_token = cls(credentials=credentials, **raw_token)
                ref_token.update(ref_token.as_dict())
                if to_file:
                    ref_token.local_cache = Path(to_file)
                return ref_token
        except Exception as e:
            print(f"Waiting for authentication... ({str(e)})")
        
        time.sleep(5)  # Wait before retrying

RefreshingToken.prompt_for_token = classmethod(patched_prompt_for_token)



app = Flask(__name__)
app.secret_key = 'f8Ugh5WbD8DrUZAwzeL5f73TBHf3Knlu'

@app.route('/')
def index():
    return "Welcome to WhatMusicDoILike? <a href='/login'>Login with Spotify</a>"


@app.route("/yt_login")
def yt_login():
    setup_oauth(
        client_id=YT_CLIENT_ID,
        client_secret=YT_SECRET,
        open_browser=True  # False if running on a server
    )
    return redirect("/yt_playlists")

@app.route("/yt_playlists")
def get_playlists():
    """Fetches playlists from the authenticated YouTube Music account."""
    # if not os.path.exists(TOKEN_FILE):
    #     return jsonify({"error": "User not authenticated. Please log in first."}), 401

    del session["oauth_token"]['_local_cache']   #for some reason dupliates for local_cache and credentials
    del session["oauth_token"]['credentials']


    ytmusic = YTMusic(session["oauth_token"], oauth_credentials=OAuthCredentials(client_id=YT_CLIENT_ID, client_secret=YT_SECRET))  # Initialize with stored token
    playlists = ytmusic.get_library_playlists(limit=10)  # Fetch user's playlists
    return jsonify(playlists)

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