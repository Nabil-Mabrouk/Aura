import os
from livekit import api
from flask import Flask, jsonify
from flask_cors import CORS  # Import CORS
from dotenv import load_dotenv

# Load credentials from the .env file
load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes on this app

# Get credentials from environment
LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')

@app.route('/get-token')
def get_token():
    """
    This endpoint generates a short-lived access token for a client.
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        return "Server credentials not configured", 500

    room_name = "aura-poc-room"
    participant_identity = "technician-alex"

    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(participant_identity) \
        .with_name("AURA Technician") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        )) \
        .to_jwt()

    return jsonify({'token': token})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)