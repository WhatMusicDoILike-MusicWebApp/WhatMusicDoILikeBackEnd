from flask import Blueprint, jsonify, request, redirect
import requests
import base64
import os
from dotenv import load_dotenv
from urllib.parse import quote
from app.models.database import db
from app.models.playlist import Playlist
from app.models.user import User
from app.models.track import Track
from app.models.playlist_has import PlaylistHas

load_dotenv('../.env')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
response_type = 'code'
show_dialog = 'true'

"""
Function to get access token
Should not actually be used, replaced by passing access token directly from db to transfer function
"""
def get_access_token():
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")

    print("Client ID:", client_id)
    print("Client Secret present:", bool(client_secret))

    if not client_id or not client_secret:
        print("Missing client ID or secret")
        return None

    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    print("Encoded auth string:", auth_base64[:10] + "...")

    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "response_text": response.text
        }


    return response.json().get('access_token')

"""
Function to search spotify for spotify specific track information
INPUTS: track String: name of track
        artist String: name of artist(s)
        access_token String

OUTPUT: List:
            name String: spotify specific name
            id String: spotify unique id for track
"""
def search_spotify(track, artist, access_token):
    """Search for an item (track, artist, album, playlist) on Spotify."""

    query = f"track:{track} artist:{artist}"

    encoded_query = quote(query)

    search_type = "track"  

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    if isinstance(access_token, dict):
        return jsonify({
            "error": "Failed to retrieve access token",
            **access_token
        }), 500


    if not access_token:
        return jsonify({
            "error": "Failed to retrieve access token",
            "client_id_loaded": os.environ.get("CLIENT_ID") is not None,
            "client_secret_loaded": os.environ.get("CLIENT_SECRET") is not None,
        }), 500



    headers = {
        'Authorization': f"Bearer {access_token}"
    }
    
    response = requests.get(f'https://api.spotify.com/v1/search?q={encoded_query}&type={search_type}&limit=3', headers=headers)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch search results from Spotify", "status_code": response.status_code}), response.status_code

    name = response.json()['tracks']['items'][0]['name']
    id = response.json()['tracks']['items'][0]['id']

    print(f"{name} {id}")
    return [name, id]

"""
Function to create a playlist on spotify
INPUTS: playlist_name String: name of source playlist
        access_token String

OUTPUT: id String: spotify unique id for playlist
"""
def create_playlist(playlist_name, access_token):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    user_id = 0

    if response.status_code == 200:
        user_info = response.json()
        user_id = user_info["id"]
        print("User ID:", user_id)
    else:
        print("Error getting user info:", response.json())
        return "Error"

    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "name": playlist_name,
        "public": False  
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print("Playlist created!")
        return response.json()["id"]
    else:
        print("Failed to create playlist:", response.json())
        return 0

"""
Function to add a track to a spotify playlist
INPUTS: playlist_id String: spotify unique playlist id
        spotify_uri String: spotify unique identifier
        access_token String

OUTPUT: None
"""
def add_track_to_playlist(playlist_id, spotify_uri, access_token):

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "uris": [f"spotify:track:{spotify_uri}"]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print("Song added to Playlist!")
        print("Snapshot ID:", response.json()["snapshot_id"])
    else:
        print("Failed to add song to playlist:", response.json())

"""
Function to get all unique track ids from our db which belong to a source playlist
INPUTS: playlist_id String: playlist db id

OUTPUT: List:
            track_id String: our own unique track id
"""
def get_playlist_songs(playlist_id):
    # Get all song IDs from the playlist
    track_ids = db.session.query(PlaylistHas.trackId).filter_by(playlistId=playlist_id).all()

    # Flatten the list of tuples into a list
    track_ids = [track_id[0] for track_id in track_ids]

    return track_ids

"""
Function to get track name and artist from our db
INPUTS: List
            track_ids String: unique track ids from our db

OUTPUT: Dictionary:
            trackName String: name of track stored in db
            artist String: artist of track
"""
def get_track_info(track_ids):
    track_info = {}
    for track_id in track_ids:
        result = db.session.query(Track.trackName, Track.artist).filter_by(trackId=track_id).first()
        track_info[result[0]] = result[1]
    
    return track_info

spotify_search_bp = Blueprint('spotify_search_bp', __name__)
# Pass userID and playlistID from json request
@spotify_search_bp.route('/spotify/transfer_playlist', methods=['POST'])
# Need playlistID, then traverse through all songs in the playlist to get name and artist and then send those to spotify search
# Pass userID and playlistID
# Using playlistID, query and get all rows (track ids) where the playlistID is = given playlistid
# Using the list of trackids, query and get all track names and artists where the row trackid in the set of given track ids
# Then we have a dictionary of track ids (key) and artists (values) Pass these to the search spotify to get their spotify ids
# The rest of the transfer playlist functionality is already implemented
def transfer_playlist():
    data = request.get_json()  # or just use: data = request.json
    userID = data.get('userID')
    playlistID = data.get('playlistID')

    if userID is None or playlistID is None:
        return jsonify({"error": "Missing userID or playlistID"}), 400
    
    access_token = db.session.query(User.spotifyAuthToken).filter_by(userId=userID)
    # refresh_token = db.session.query(User.spotifyRefreshToken).filter_by(userId=userID)

    # list of all track ids which belong to source playlist
    lst_track_ids = get_playlist_songs(playlistID)
    # get the name of the source playlist
    playlist_name = db.session.query(Playlist.playlistName).filter_by(playlistId=playlistID).first()
    playlist_name = playlist_name[0] if playlist_name else "Untitled Playlist"

    # dictionary of track names (key) and artists (value)
    playlist_tracks = get_track_info(lst_track_ids)

    new_playlst_id_spotify = create_playlist(playlist_name, access_token)

    new_playlist = Playlist(playlistName=playlist_name, playlistUrl=new_playlst_id_spotify, playlistOwnerId=userID)
    db.session.add(new_playlist)
    db.session.commit()

    new_playlist_id = new_playlist.playlistId

    for track, artist in playlist_tracks.items():
        # track content = [name, id]
        track_content = search_spotify(track, artist, access_token)

        official_name = track_content[0]
        spotify_id = track_content[1]

        song = Track.query.filter_by(trackName=official_name, artist=artist).first()

        if not song:
            song = Track(trackName=official_name, artist=artist, trackUrl=spotify_id)
            db.session.add(song)
            db.session.commit()  
        
        playlist_song = PlaylistHas(trackId=song.trackId, playlistId=new_playlist_id)
        db.session.add(playlist_song)
        db.session.commit()

        add_track_to_playlist(new_playlst_id_spotify, spotify_id, access_token)
    
    return "Playlist Transferred"
    


        
