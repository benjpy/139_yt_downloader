import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add parent directory to path so we can import downloader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import downloader

class TestDownloaderOptions(unittest.TestCase):
    def test_options_audio_only(self):
        opts = downloader.get_yt_dlp_options("downloads", "Audio Only")
        self.assertEqual(opts['format'], 'bestaudio/best')
        self.assertTrue(any(pp['key'] == 'FFmpegExtractAudio' for pp in opts['postprocessors']))

    def test_options_transcript(self):
        opts = downloader.get_yt_dlp_options("downloads", "Transcript")
        self.assertTrue(opts['skip_download'])
        self.assertTrue(opts['writesubtitles'])

    def test_options_video_medium(self):
        opts = downloader.get_yt_dlp_options("downloads", "Video + Audio", quality="Medium (720p)")
        self.assertIn("height<=720", opts['format'])

    @patch('downloader.yt_dlp.YoutubeDL')
    def test_download_content_success_mock(self, mock_ydl):
        # Setup mock
        instance = mock_ydl.return_value
        instance.__enter__.return_value = instance
        instance.extract_info.return_value = {'title': 'Test Video', 'ext': 'mp4'}
        
        # Mock os.listdir and os.path.join to simulate file finding
        with patch('os.listdir', return_value=['Test Video.mp4']), \
             patch('os.path.exists', return_value=True), \
             patch('os.makedirs'):
             
             result = downloader.download_content("http://dummy", "downloads", "Video + Audio")
             self.assertEqual(result['status'], 'success')
             self.assertTrue(result['file_path'].endswith('Test Video.mp4'))

if __name__ == '__main__':
    unittest.main()
