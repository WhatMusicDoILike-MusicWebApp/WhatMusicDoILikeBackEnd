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

spotify_search = Blueprint('spotify_search', __name__)

@spotify_search.route('/spotify/search', methods=['GET'])
def search_item():
    request_data = request.get_json()
    print(request_data)

    
    return "Success"