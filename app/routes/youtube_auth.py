import os
from flask import Blueprint, redirect, jsonify, session
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
                time.sleep(0.5)  # Small delay before closing tab
                if platform.system() == "Darwin":  # macOS
                    pyautogui.hotkey("command", "w")
                else:  # Windows/Linux
                    pyautogui.hotkey("ctrl", "w")

                print("Authentication successful. Tab closed.")
                return ref_token
        except Exception as e:
            print(f"Waiting for authentication... ({str(e)})")
        
        time.sleep(0.5)  # Wait before retrying

RefreshingToken.prompt_for_token = classmethod(patched_prompt_for_token)



@youtube_auth_bp.route("/youtube/yt_auth", methods=['POST'])
def yt_login():
    token = setup_oauth(
        client_id=YT_CLIENT_ID,
        client_secret=YT_SECRET,
        open_browser=True  
    )

    if token:
        session["oauth_token"] = token  
        session.modified = True  

        
    ytmusic = YTMusic(session["oauth_token"].as_dict(), oauth_credentials=OAuthCredentials(client_id=YT_CLIENT_ID, client_secret=YT_SECRET))  # Initialize with stored token
    playlists = ytmusic.get_library_playlists(limit=10)  # Fetch user's playlists
    return jsonify(playlists)
