import streamlit as st
import yt_dlp
import os
import shutil

# Set page config
st.set_page_config(page_title="YouTube Video Downloader", page_icon="📺", layout="centered")

# Custom CSS for modern aesthetic
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #ffffff;
        border-color: #4b4b4b;
    }
    .stSelectbox > div > div > div {
        background-color: #262730;
        color: #ffffff;
    }
    h1 {
        color: #ff4b4b;
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stButton > button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #ff3333;
        border-color: #ff3333;
    }
    .status-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #1e1e1e;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📺 YouTube Video Downloader")
st.markdown("Download videos or audio from YouTube in high quality.")

# URL Input
url = st.text_input("Paste YouTube URL here:", placeholder="https://www.youtube.com/watch?v=...")

# Options in columns
col1, col2 = st.columns(2)

with col1:
    download_type = st.radio("Download Type", ["Video + Audio", "Audio Only", "Transcript", "Transcript (Plain Text)", "Comments"])

with col2:
    if download_type == "Video + Audio":
        quality = st.selectbox("Resolution", ["Top (Best Available)", "Medium (720p)", "Low (360p)"])
    elif download_type == "Audio Only":
        quality = None
        st.info("Audio will be downloaded as MP3.")
    elif download_type == "Transcript":
        quality = None
        st.info("Transcript will be downloaded as VTT/SRT text file (with timestamps).")
    elif download_type == "Transcript (Plain Text)":
        quality = None
        st.info("Transcript will be downloaded as a plain text file (no timestamps).")
    elif download_type == "Comments":
        quality = None
        st.info("Top comments will be saved to a CSV file.")

# Download Button
if st.button("Download", use_container_width=True):
    if not url:
        st.error("Please enter a valid URL.")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # Create downloads directory if not exists
            download_path = "downloads"
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            
            # Configure yt-dlp options
            ydl_opts = {
                'outtmpl': f'{download_path}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                # Fix for 403 Forbidden: Use a real browser user agent and disable cache
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'auto',
                'source_address': '0.0.0.0',
            }
            
            # Add robust headers
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }

            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%', '')
                        progress_bar.progress(float(p) / 100)
                        status_text.text(f"Downloading... {d.get('_percent_str')}")
                    except:
                        pass
                elif d['status'] == 'finished':
                    status_text.text("Download complete! Processing...")
                    progress_bar.progress(1.0)

            ydl_opts['progress_hooks'] = [progress_hook]

            # Specific Logic for each type
            if download_type == "Audio Only":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            elif download_type == "Transcript" or download_type == "Transcript (Plain Text)":
                ydl_opts.update({
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitlesformat': 'vtt',
                    'subtitleslangs': ['en'],
                })
            elif download_type == "Comments":
                ydl_opts.update({
                    'skip_download': True,
                    'getcomments': True,
                })
            else: # Video + Audio
                if "Top" in quality:
                    ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})
                elif "Medium" in quality:
                    ydl_opts.update({'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'})
                elif "Low" in quality:
                    ydl_opts.update({'format': 'worstvideo[ext=mp4]+bestaudio[ext=m4a]/worst[ext=mp4]/worst'})

            
            # Clean up downloads directory to ensure no collision
            for f in os.listdir(download_path):
                try:
                    os.remove(os.path.join(download_path, f))
                except:
                    pass

            with st.spinner("Fetching data..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    video_title = info_dict.get('title', 'video')
            
            # Handle Post-Download/Processing logic
            downloaded_file_path = None
            
            if download_type == "Comments":
                # Process comments to CSV
                comments = info_dict.get('comments', [])
                if not comments:
                    st.warning("No comments found or comments are disabled.")
                else:
                    import csv
                    csv_filename = f"{video_title}_comments.csv"
                    # Sanitize filename
                    csv_filename = "".join([c for c in csv_filename if c.isalpha() or c.isdigit() or c in " ._-"]).strip()
                    csv_path = os.path.join(download_path, csv_filename)
                    
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['author', 'date', 'text', 'likes']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for comment in comments:
                            writer.writerow({
                                'author': comment.get('author'),
                                'date': comment.get('timestamp'), # timestamp is unix
                                'text': comment.get('text'),
                                'likes': comment.get('like_count')
                            })
                    downloaded_file_path = csv_path
                    status_text.success("Comments extracted successfully!")

            elif download_type == "Transcript" or download_type == "Transcript (Plain Text)":
                 # Find the subtitle file
                files = os.listdir(download_path)
                # Look for .vtt files
                sub_files = [f for f in files if f.endswith('.vtt')]
                if sub_files:
                    vtt_path = os.path.join(download_path, sub_files[0])
                    
                    if download_type == "Transcript (Plain Text)":
                        import re
                        # Convert VTT to TXT
                        txt_filename = sub_files[0].replace('.vtt', '.txt')
                        txt_path = os.path.join(download_path, txt_filename)
                        
                        unique_lines = []
                        last_line = ""
                        
                        with open(vtt_path, 'r', encoding='utf-8') as f_vtt:
                            for line in f_vtt:
                                line = line.strip()
                                # Skip metadata, timestamps (contain -->), and empty lines
                                if "WEBVTT" in line or "-->" in line or not line:
                                    continue
                                # Skip extra metadata headers often found in yt-dlp converted files
                                if line.startswith("Kind:") or line.startswith("Language:"):
                                    continue
                                # Skip simple numbers often acting as IDs
                                if line.isdigit():
                                    continue
                                
                                # Remove HTML-like tags (e.g. <c>, <00:...>)
                                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                                
                                if not clean_line:
                                    continue

                                # Dedup consecutive lines
                                if clean_line != last_line:
                                    unique_lines.append(clean_line)
                                    last_line = clean_line
                        
                        with open(txt_path, 'w', encoding='utf-8') as f_txt:
                            f_txt.write("\n".join(unique_lines))
                        
                        downloaded_file_path = txt_path
                    else:
                        downloaded_file_path = vtt_path
                else:
                    st.error("No transcript found (none available in English).")

            else: # Audio or Video
                # Find the downloaded file
                files = os.listdir(download_path)
                # Filter out the transcript files if any accidentally downloaded or remain
                media_files = [f for f in files if not f.endswith('.vtt') and not f.endswith('.csv')]
                
                if media_files:
                    downloaded_file_name = media_files[0]
                    downloaded_file_path = os.path.join(download_path, downloaded_file_name)
                else:
                    downloaded_file_path = None

            if downloaded_file_path and os.path.exists(downloaded_file_path):
                status_text.success(f"File ready: {os.path.basename(downloaded_file_path)}")
                
                with open(downloaded_file_path, "rb") as f:
                    file_data = f.read()
                    
                    # Determine MIME type based on extension
                    mime_type = "application/octet-stream"
                    if downloaded_file_path.endswith(".mp4"):
                        mime_type = "video/mp4"
                    elif downloaded_file_path.endswith(".mp3"):
                        mime_type = "audio/mpeg"
                    elif downloaded_file_path.endswith(".csv"):
                        mime_type = "text/csv"
                    elif downloaded_file_path.endswith(".vtt"):
                        mime_type = "text/vtt"
                    elif downloaded_file_path.endswith(".txt"):
                        mime_type = "text/plain"

                    st.download_button(
                        label=f"Download {os.path.basename(downloaded_file_path)}",
                        data=file_data,
                        file_name=os.path.basename(downloaded_file_path),
                        mime=mime_type
                    )
                
                # Cleanup (Optional: remove file after read? Streamlit re-runs script, 
                # so we might want to keep it until button clicked. 
                # But button click triggers re-run. 
                # Better to clean up older files periodically or rely on user to not span.)
                # For this simple app, we leave it or clean up on next run.
            else:
                st.error("Error: Could not locate downloaded file.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
