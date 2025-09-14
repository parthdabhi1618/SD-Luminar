try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    _HAS_GOOGLE_API = True
except Exception:
    build = None
    _HAS_GOOGLE_API = False
import os
import json
from pytube import YouTube

class YouTubeDownloader:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        # Initialize YouTube Data API client only if the library is available and api_key provided
        self.youtube = None
        if _HAS_GOOGLE_API and self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception:
                self.youtube = None
    
    def get_video_info(self, video_url):
        """Get video information using YouTube Data API."""
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return None
        # Prefer YouTube Data API if available
        if self.youtube:
            try:
                request = self.youtube.videos().list(
                    part="snippet,contentDetails",
                    id=video_id
                )
                response = request.execute()
                if response.get('items'):
                    video_data = response['items'][0]
                    thumb = video_data['snippet']['thumbnails'].get('maxres', {}) or video_data['snippet']['thumbnails'].get('high', {})
                    return {
                        'id': video_id,
                        'title': video_data['snippet']['title'],
                        'thumbnail': thumb.get('url'),
                        'duration': video_data['contentDetails']['duration']
                    }
            except Exception as e:
                print(f"Error fetching video info via API: {e}")
        # Fallback to pytube for metadata
        try:
            yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
            return {
                'id': video_id,
                'title': yt.title,
                'thumbnail': yt.thumbnail_url,
                'duration': yt.length
            }
        except Exception as e:
            print(f"Fallback metadata fetch failed: {e}")
            return None
    
    def _extract_video_id(self, url):
        """Extract video ID from various YouTube URL formats."""
        import re
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_download_url(self, video_id, quality='high'):
        """Get direct download URL using pytube (fallback for actual download)."""
        from pytube import YouTube
        try:
            yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
            if quality == 'high':
                stream = yt.streams.get_highest_resolution()
            else:
                stream = yt.streams.get_lowest_resolution()
            return stream.url
        except Exception as e:
            print(f"Error getting download URL: {e}")
            return None