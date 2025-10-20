#!/usr/bin/env python3
"""
YouTube uploader module - Handles uploading videos to YouTube as Shorts.
"""

import logging
import os
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# YouTube Shorts video category (22 = People & Blogs, adjust as needed)
DEFAULT_CATEGORY_ID = '22'


class YouTubeUploader:
    """Handles YouTube authentication and video uploads."""

    def __init__(self, credentials_file: str = 'client_secrets.json', token_file: str = 'token.pickle'):
        """
        Initialize the YouTube uploader.

        Args:
            credentials_file: Path to OAuth2 client secrets JSON file
            token_file: Path to save/load the authentication token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube = None

    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth2.

        Returns:
            True if authentication successful, False otherwise
        """
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing authentication token...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    logger.error("Please download OAuth2 credentials from Google Cloud Console")
                    logger.error("https://console.cloud.google.com/apis/credentials")
                    return False

                try:
                    logger.info("Starting OAuth2 authentication flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Authentication successful!")
                except Exception as e:
                    logger.error(f"Authentication failed: {e}")
                    return False

            # Save the credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        # Build the YouTube API client
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            logger.debug("YouTube API client initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to build YouTube API client: {e}")
            return False

    def upload_video(
        self,
        video_file: Path,
        title: str,
        description: str = "",
        tags: Optional[list] = None,
        category_id: str = DEFAULT_CATEGORY_ID,
        privacy_status: str = "private",
        made_for_kids: bool = False,
        notify_subscribers: bool = False
    ) -> Optional[str]:
        """
        Upload a video to YouTube.

        Args:
            video_file: Path to the video file to upload
            title: Video title
            description: Video description
            tags: List of tags/keywords
            category_id: YouTube category ID
            privacy_status: 'public', 'private', or 'unlisted'
            made_for_kids: Whether the video is made for kids (required by YouTube)
            notify_subscribers: Whether to notify subscribers about the upload

        Returns:
            Video ID if successful, None otherwise
        """
        if not self.youtube:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        if not video_file.exists():
            logger.error(f"Video file not found: {video_file}")
            return None

        # Default tags if none provided
        if tags is None:
            tags = ['Shorts', 'YouTube Shorts']

        # Add #Shorts to description if not present (important for YouTube Shorts detection)
        if '#Shorts' not in description and '#shorts' not in description:
            description = f"{description}\n\n#Shorts" if description else "#Shorts"

        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # YouTube title limit
                'description': description[:5000],  # YouTube description limit
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids
            },
            'notifySubscribers': notify_subscribers
        }

        # Prepare the media file upload
        media = MediaFileUpload(
            str(video_file),
            mimetype='video/*',
            resumable=True,
            chunksize=1024 * 1024  # 1MB chunks
        )

        try:
            logger.info(f"Uploading video: {video_file.name}")
            logger.info(f"  Title: {title}")
            logger.info(f"  Privacy: {privacy_status}")

            # Execute the upload
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"  Upload progress: {progress}%")

            video_id = response['id']
            video_url = f"https://www.youtube.com/shorts/{video_id}"

            logger.info(f"✓ Upload successful!")
            logger.info(f"  Video ID: {video_id}")
            logger.info(f"  URL: {video_url}")

            return video_id

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            if e.resp.status == 403:
                logger.error("Permission denied. Check API quota and OAuth scopes.")
            elif e.resp.status == 401:
                logger.error("Authentication failed. Try deleting token.pickle and re-authenticating.")
            return None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    def upload_short(
        self,
        video_file: Path,
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[list] = None,
        privacy_status: str = "private"
    ) -> Optional[str]:
        """
        Convenience method to upload a YouTube Short.

        Args:
            video_file: Path to the video file to upload
            title: Video title (defaults to filename if not provided)
            description: Video description
            tags: List of tags/keywords
            privacy_status: 'public', 'private', or 'unlisted'

        Returns:
            Video ID if successful, None otherwise
        """
        if title is None:
            title = video_file.stem.replace('_', ' ').title()

        return self.upload_video(
            video_file=video_file,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            made_for_kids=False,
            notify_subscribers=False
        )


def upload_to_youtube(
    video_file: Path,
    title: Optional[str] = None,
    description: str = "",
    tags: Optional[list] = None,
    privacy_status: str = "private",
    credentials_file: str = 'client_secrets.json',
    token_file: str = 'token.pickle'
) -> Optional[str]:
    """
    Simplified function to upload a video to YouTube.

    Args:
        video_file: Path to the video file
        title: Video title (defaults to filename)
        description: Video description
        tags: List of tags
        privacy_status: 'public', 'private', or 'unlisted'
        credentials_file: Path to OAuth2 credentials
        token_file: Path to token cache file

    Returns:
        Video ID if successful, None otherwise
    """
    uploader = YouTubeUploader(credentials_file, token_file)

    if not uploader.authenticate():
        return None

    return uploader.upload_short(
        video_file=video_file,
        title=title,
        description=description,
        tags=tags,
        privacy_status=privacy_status
    )
