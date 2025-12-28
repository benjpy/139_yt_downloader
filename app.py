import streamlit as st
import os
import styles
import downloader

# Set page config
st.set_page_config(page_title="YouTube Video Downloader", page_icon="📺", layout="centered")

# Custom CSS for modern aesthetic
st.markdown(styles.CSS, unsafe_allow_html=True)

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
        
        # Callback to update UI from downloader
        def update_progress(percent, text=None):
            progress_bar.progress(percent)
            if text:
                status_text.text(text)

        with st.spinner("Fetching data..."):
            result = downloader.download_content("downloads", url, download_type, quality, update_progress)

        # Handle Result
        if result['status'] == 'success':
            file_path = result['file_path']
            filename = os.path.basename(file_path)
            status_text.success(f"File ready: {filename}")
            
            with open(file_path, "rb") as f:
                file_data = f.read()
                
                # Determine MIME type based on extension
                mime_type = "application/octet-stream"
                if filename.endswith(".mp4"):
                    mime_type = "video/mp4"
                elif filename.endswith(".mp3"):
                    mime_type = "audio/mpeg"
                elif filename.endswith(".csv"):
                    mime_type = "text/csv"
                elif filename.endswith(".vtt"):
                    mime_type = "text/vtt"
                elif filename.endswith(".txt"):
                    mime_type = "text/plain"

                st.download_button(
                    label=f"Download {filename}",
                    data=file_data,
                    file_name=filename,
                    mime=mime_type
                )
        elif result['status'] == 'warning':
            st.warning(result['message'])
        else: # error
            st.error(f"An error occurred: {result.get('message', 'Unknown error')}")
