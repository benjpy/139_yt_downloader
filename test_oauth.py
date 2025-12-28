import yt_dlp
import sys
from io import StringIO

def test_oauth():
    # Capture stdout to see if we can catch the OAuth message
    
    # Options for OAuth
    ydl_opts = {
        'username': 'oauth2',
        'password': '',
        'quiet': False, # We need output
    }
    
    url = "https://www.youtube.com/shorts/Kre2eDgdFDI"
    
    print("Starting OAuth test...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    test_oauth()
