import os
from flask import Blueprint, request, jsonify, session
from app.models.database import db
import time
from ytmusicapi import OAuthCredentials, YTMusic, setup_oauth
from ytmusicapi.auth.oauth.credentials import Credentials
from ytmusicapi.auth.oauth.token import RefreshingToken
import webbrowser
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import platform
import pyautogui

from app.models.playlist import Playlist
from app.models.playlist_has import PlaylistHas
from app.models.song import Song
from app.models.user import User


load_dotenv('.env')


YT_CLIENT_ID = os.getenv("YT_CLIENT")
YT_SECRET = os.getenv("YT_SECRET")

youtube_auth_bp = Blueprint('youtube_auth_bp', __name__)

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
                if platform.system() == "Darwin":  # macOS
                    pyautogui.hotkey("command", "w")
                else:  # Windows/Linux
                    pyautogui.hotkey("ctrl", "w")

                print("Authentication successful. Tab closed.")
                return ref_token
        except Exception as e:
            print(f"Waiting for authentication... ({str(e)})")
        
        time.sleep(0.1)  # Wait before retrying

RefreshingToken.prompt_for_token = classmethod(patched_prompt_for_token)


def store_yt_songs_in_db(playlists, user_id):
    "Stores playlist and songs in db"
    user = User.query.filter_by(userId=user_id).first()
    if not user:
            print(f"User with ID {user_id} does not exist")
            return False
    
    for playlist in playlists:
        new_playlist = Playlist(
                playlistName=playlist['title'],
                playlistOwnerId=user_id
        )

        db.session.add(new_playlist)
        db.session.flush()  

        playlist_id = new_playlist.playlistId

        for track in playlist['tracks']:
            print("---------Name----------------")
            print(track['title'])       
            print("---------Artist----------------")                
            print(track['artists'][0]['name'])       
            existing_song = Song.query.filter_by(
                trackName=track['title'],
                artist=track['artists'][0]['name']
            ).first()
            
            if existing_song:
                song_id = existing_song.songId
            else:
                new_song = Song(
                    trackName=track['title'],
                    artist=track['artists'][0]['name']
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


        


@youtube_auth_bp.route("/youtube/yt_auth", methods=['POST'])
def yt_login():
    request_data = request.get_json()
    token = setup_oauth(
        client_id=YT_CLIENT_ID,
        client_secret=YT_SECRET,
        open_browser=True  
    )

    if token:
        session["oauth_token"] = token  
        session.modified = True  

    clerk_unique_id = request_data['userId']
    print(clerk_unique_id)
        
    ytmusic = YTMusic(session["oauth_token"].as_dict(), oauth_credentials=OAuthCredentials(client_id=YT_CLIENT_ID, client_secret=YT_SECRET))  # Initialize with stored token
    playlists = ytmusic.get_library_playlists()  # Fetch user's playlists

    list_of_playlist = []

    for playlist in playlists:
        list_of_playlist.append(ytmusic.get_playlist(playlist["playlistId"]))
            
    result = store_yt_songs_in_db(list_of_playlist, clerk_unique_id)

    if result:
        return jsonify({"message": "Songs stored successfully"}), 200
    else:
        return jsonify({"message": "Error storing songs"}), 400


