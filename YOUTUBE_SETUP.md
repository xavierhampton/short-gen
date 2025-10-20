# YouTube API Setup Guide

This guide walks you through setting up YouTube Data API v3 credentials to enable automatic video uploads.

## Prerequisites

- A Google account
- Access to Google Cloud Console
- A YouTube channel linked to your Google account

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "shortgen-uploader")
5. Click "Create"

## Step 2: Enable YouTube Data API v3

1. In your project, go to "APIs & Services" > "Library"
2. Search for "YouTube Data API v3"
3. Click on it and click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace)
3. Click "Create"
4. Fill in the required fields:
   - App name: `shortgen`
   - User support email: your email
   - Developer contact email: your email
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Search for and add: `https://www.googleapis.com/auth/youtube.upload`
8. Click "Save and Continue"
9. On "Test users", add your Google account email
10. Click "Save and Continue"

## Step 4: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as the application type
4. Give it a name (e.g., "shortgen-desktop")
5. Click "Create"
6. Click "Download JSON" on the confirmation dialog
7. Rename the downloaded file to `client_secrets.json`
8. Move it to your shortgen project root directory

## Step 5: First-Time Authentication

When you first run shortgen with the `--upload` flag:

```bash
python src/main.py input.mp4 --upload
```

1. Your browser will open automatically
2. Sign in with your Google account
3. Review the permissions (YouTube upload access)
4. Click "Allow"
5. You'll see "The authentication flow has completed"
6. Close the browser tab

A `token.pickle` file will be created in your project directory. This stores your authentication token for future uploads (you won't need to sign in again).

## Step 6: Test Upload

Try uploading a test video:

```bash
python src/main.py test_video.mp4 --upload --title "Test Short" --privacy private
```

If successful, you'll see:
```
✓ Upload successful!
  Video ID: abc123xyz
  URL: https://www.youtube.com/shorts/abc123xyz
```

## Docker Usage

When using Docker, you need to mount both credential files:

```bash
docker run --rm \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/client_secrets.json:/app/client_secrets.json:ro \
  -v $(pwd)/token.pickle:/app/token.pickle \
  shortgen /app/videos --upload
```

Note: First-time authentication in Docker requires interactive mode and port forwarding:

```bash
docker run -it --rm \
  -p 8080:8080 \
  -v $(pwd)/client_secrets.json:/app/client_secrets.json \
  -v $(pwd)/token.pickle:/app/token.pickle \
  shortgen --help
```

Then run with `--upload` after authentication completes.

## Security Notes

- **Never commit** `client_secrets.json` or `token.pickle` to version control
- Add them to your `.gitignore`:
  ```
  client_secrets.json
  token.pickle
  ```
- Keep these files secure - they provide access to upload videos to your channel
- If compromised, revoke access in [Google Account Security](https://myaccount.google.com/permissions)

## Quota Limits

YouTube Data API has daily quotas:
- Default quota: 10,000 units per day
- Video upload cost: ~1,600 units per upload
- This allows ~6 uploads per day with default quota

To request a quota increase:
1. Go to Google Cloud Console
2. Navigate to "APIs & Services" > "Quotas"
3. Find "YouTube Data API v3"
4. Request a quota increase (requires explanation of use case)

## Troubleshooting

### "Credentials file not found"
- Ensure `client_secrets.json` is in the project root
- Use `--credentials` flag to specify a custom path

### "Authentication failed"
- Delete `token.pickle` and re-authenticate
- Check that your Google account has a YouTube channel
- Verify the OAuth consent screen test users include your account

### "Permission denied (403)"
- Check API quota hasn't been exceeded
- Verify YouTube Data API v3 is enabled
- Ensure OAuth scopes include `youtube.upload`

### "Invalid grant"
- Token may have expired or been revoked
- Delete `token.pickle` and re-authenticate

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [OAuth2 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [YouTube API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)
