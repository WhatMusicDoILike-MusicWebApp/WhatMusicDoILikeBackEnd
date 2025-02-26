from flask import Blueprint, jsonify, request
from app.models.database import db

import os
from datetime import datetime
from flask import Flask, redirect, session
import requests
import urllib.parse
import json

from app.models import User, Playlist, Song, PlaylistHas

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
API_BASE_URL = os.getenv("API_BASE_URL")

playlist_map = {}
user_credentials = {}

spotify_auth_bp = Blueprint('spotify_auth_bp', __name__)

@spotify_auth_bp.route('/spotify/fetchUserData', methods=['POST', 'GET'])
def fetch_user_spotify_data():

    global user_credentials 
    user_credentials = request.get_json()

    print('\ncallback reached\n')


    if 'error' in request.get_json():
        return jsonify({"error": request.get_json()['error']})

    if 'code' in request.get_json():

        fetch_auth_token(request.get_json()['code'])

        return get_playlists()
    
    return "Failure"

# get all playlist ids and names
def get_playlists():

    print("getPlaylists reached")
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    playlist_ids = [playlist['id'] for playlist in playlists.get('items', [])]
    playlist_names = [playlist['name'] for playlist in playlists.get('items', [])]

    global playlist_map
    for id, names in zip(playlist_ids, playlist_names):
        playlist_map[(id, names)] = None


    print(playlist_map)

    return get_playlists_items()

# get all tracks from all playlists
def get_playlists_items():  
    print("getPlaylistItems reached")  
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    global playlist_map
    total_tracks = 0

    for (id,name) in playlist_map.keys():
        offset = 0
        all_tracks = []
        while True:
            response = requests.get(API_BASE_URL + f'playlists/{id}/tracks?offset={offset}&fields=items(track(name,artists(name)))', headers=headers)
            tracks = response.json()

            track_items = tracks.get('items', [])

            if not track_items:
                break

            track_items = tracks.get('items', [])
            all_tracks.append(track_items)

            total_tracks += len(track_items)

            offset += 100

        playlist_map[(id,name)] = (len(all_tracks), all_tracks)

    user = User.query.filter_by(userId=user_credentials['userId']).first()
    if not user:
        return "Error: User does not exist"
    
    for (id, name) in playlist_map:
        track_names = []
        # Add playlist to playlist table
        new_playlist = Playlist(
            playlistName=name,
            playlistOwnerId=user_credentials['userId']
        )

        db.session.add(new_playlist)

        data = playlist_map[(id, name)][1]

        if data == []:
            print("Empty Playlist")
            playlist_map[(id,name)] = (0, [])
            continue

        all_tracks = data[0]
        for track_info in all_tracks:
            track = track_info['track']
            track_name = track['name']
            track_names.append(track_name)

            artists = [artist['name'] for artist in track['artists']]

            new_track = Song(
                trackName = track_name,
                artist = ', '.join(artists)
            )

            db.session.add(new_track)
        
        db.session.commit()

        playlist_id = db.session.query(Playlist.playlistId).filter_by(playlistName=name).first()
        playlist_id = playlist_id[0]
        for track in track_names:
            track_id = db.session.query(Song.songId).filter_by(trackName=track).first()
            track_id = track_id[0]

            # CHECK FOR DUPLICATE
            exists = db.session.query(PlaylistHas).filter_by(
                playlistId=playlist_id, songId=track_id
            ).first()

            if not exists:
                playlist_has = PlaylistHas(playlistId=playlist_id, songId=track_id)
                db.session.add(playlist_has)
                db.session.commit()

    return playlist_map

def fetch_auth_token(code):
    req_body = {
        'code': code,
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

    return "Success"

