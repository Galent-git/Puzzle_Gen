"""
YouTube API Authentication Helper
---------------------------------
This module handles OAuth 2.0 authentication for YouTube Data API access.

Responsibilities:
1. Load stored credentials from a pickle file (if available).
2. Refresh credentials if expired and refresh token is present.
3. Run interactive OAuth flow if no valid credentials exist.
4. Save new or refreshed credentials for future use.
5. Return an authenticated YouTube API service client.

Usage:
    from auth import get_authenticated_service
    youtube_service = get_authenticated_service()

Configuration:
    All paths, scopes, and API settings are loaded from `upload_config.py`.
"""
# uploader/auth.py

import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Import the sibling config file
import upload_config

def get_authenticated_service():
    """
    Authenticates with the YouTube API using OAuth 2.0.

    Handles token loading, refreshing, and saving for subsequent runs.
    If no valid credentials are found, it initiates the user login flow.

    Returns:
        googleapiclient.discovery.Resource: An authenticated YouTube API service object.
    """
    credentials = None
    if upload_config.TOKEN_PICKLE_PATH.exists():
        with open(upload_config.TOKEN_PICKLE_PATH, 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing expired credentials...")
            credentials.refresh(Request())
        else:
            print("No valid credentials found. Starting authentication flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(upload_config.CLIENT_SECRETS_FILE), 
                upload_config.SCOPES
            )
            credentials = flow.run_local_server(port=0)
            print("Authentication successful.")
        
        # Save the credentials for the next run
        with open(upload_config.TOKEN_PICKLE_PATH, 'wb') as token:
            pickle.dump(credentials, token)
            print(f"Credentials saved to: {upload_config.TOKEN_PICKLE_PATH}")
    
    print("YouTube API service authenticated successfully.")
    return build(
        upload_config.API_NAME, 
        upload_config.API_VERSION, 
        credentials=credentials
    )