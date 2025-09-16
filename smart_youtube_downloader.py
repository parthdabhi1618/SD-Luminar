from pytube import YouTube
from googleapiclient.discovery import build
import os
import json
from typing import Optional, Dict, Any

class SmartYouTubeDownloader:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key for enhanced metadata."""
        self.api_key = api_key
        self.youtube_api = build('youtube', 'v3', developerKey=api_key) if api_key else None
        
    def _get_video_id(self, url: str) -> Optional[str]:
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

    def _get_video_info_api(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video information using YouTube Data API if available."""
        if not self.youtube_api:
            return None
            
        try:
            request = self.youtube_api.videos().list(
                part="snippet,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                video_data = response['items'][0]
                return {
                    'title': video_data['snippet']['title'],
                    'description': video_data['snippet']['description'],
                    'thumbnail': video_data['snippet']['thumbnails']['maxres']['url'],
                    'duration': video_data['contentDetails']['duration']
                }
        except Exception as e:
            print(f"API Error: {e}")
            return None
            
    def _get_streams(self, url: str) -> Optional[YouTube]:
        """Get video streams using pytube."""
        try:
            yt = YouTube(url)
            return yt
        except Exception as e:
            print(f"Pytube Error: {e}")
            return None
            
    def download_video(self, url: str, output_path: str, quality: str = 'high') -> Dict[str, Any]:
        """Download video with enhanced error handling and progress tracking."""
        video_id = self._get_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
            
        # Try to get enhanced metadata first
        info = self._get_video_info_api(video_id) or {}
        
        # Get video streams
        yt = self._get_streams(url)
        if not yt:
            raise RuntimeError("Failed to fetch video streams")
            
        # Update info with basic metadata if API wasn't available
        info.update({
            'title': info.get('title', yt.title),
            'length': yt.length,
            'author': yt.author
        })
        
        # Select stream based on quality
        if quality == 'high':
            stream = yt.streams.get_highest_resolution()
        else:
            stream = yt.streams.get_lowest_resolution()
            
        if not stream:
            raise RuntimeError("No suitable stream found")
            
        # Download the video
        try:
            file_path = stream.download(output_path=output_path)
            info['file_path'] = file_path
            info['file_size'] = os.path.getsize(file_path)
            return info
        except Exception as e:
            raise RuntimeError(f"Download failed: {str(e)}")
            
    def get_preview_info(self, url: str) -> Dict[str, Any]:
        """Get video preview information without downloading."""
        video_id = self._get_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
            
        # Try API first for better metadata
        info = self._get_video_info_api(video_id)
        if info:
            return info
            
        # Fallback to pytube
        yt = self._get_streams(url)
        if not yt:
            raise RuntimeError("Failed to fetch video information")
            
        return {
            'title': yt.title,
            'thumbnail': yt.thumbnail_url,
            'length': yt.length,
            'author': yt.author
        }