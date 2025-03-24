from flask import Blueprint, jsonify, request, redirect
import requests
import base64
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv('../.env')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
response_type = 'code'
show_dialog = 'true'


spotify_search_bp = Blueprint('spotify_search_bp', __name__)

@spotify_search_bp.route('/spotify/auth_code', methods=['GET'])
def get_authorization_code():
    CLIENT_ID = os.environ.get('CLIENT_ID')

    auth_url = f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&show_dialog=True"
    print(auth_url)
    return redirect(auth_url)

    
# Function to get an access token
def get_spotify_access_token(code):
    """Fetch authentication token from Spotify API"""
    REDIRECT_URI = 'http://localhost:5173/dashboard'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

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
        response = requests.post(TOKEN_URL, data=urlencode(req_body), headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@spotify_search_bp.route('/spotify/search', methods=['GET'])
def search_spotify():
    """Search for an item (track, artist, album, playlist) on Spotify."""
    search = request.get_json()
    query = search['q']
    search_type = search['type']  # Default to searching for tracks

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    access_token = os.environ.get("TOKEN")

    headers = {
        'Authorization': f"Bearer {access_token}"
    }
    
    response = requests.get(f'https://api.spotify.com/v1/search?q={query}&type={search_type}&limit=3', headers=headers)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch search results from Spotify", "status_code": response.status_code}), response.status_code


    name = response.json()['tracks']['items'][0]['name']
    id = response.json()['tracks']['items'][0]['id']
    return [name, id]
