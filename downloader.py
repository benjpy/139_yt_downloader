import os
import re
import csv
import yt_dlp

def get_yt_dlp_options(download_path, download_type, quality=None, progress_hook=None):
    """
    Generate yt-dlp options based on download type and quality.
    """
    ydl_opts = {
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }
    
    if progress_hook:
        ydl_opts['progress_hooks'] = [progress_hook]

    if download_type == "Audio Only":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif download_type in ["Transcript", "Transcript (Plain Text)"]:
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
        # Safety check if quality is None
        if not quality: 
            quality = "Top"
            
        if "Top" in quality:
            ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})
        elif "Medium" in quality:
            ydl_opts.update({'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'})
        elif "Low" in quality:
            ydl_opts.update({'format': 'worstvideo[ext=mp4]+bestaudio[ext=m4a]/worst[ext=mp4]/worst'})

    return ydl_opts


def download_content(url, download_path, download_type, quality=None, progress_callback=None):
    """
    Main download function.
    Returns a dictionary with result info (status, file_path, message).
    """
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    # Clean up directory
    for f in os.listdir(download_path):
        try:
            os.remove(os.path.join(download_path, f))
        except:
            pass

    # Progress hook wrapper to adapt to our callback signature
    def progress_hook_wrapper(d):
        if progress_callback:
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '0%').replace('%', '')
                    progress_callback(float(p)/100, f"Downloading... {d.get('_percent_str')}")
                except:
                    pass
            elif d['status'] == 'finished':
                progress_callback(1.0, "Download complete! Processing...")

    ydl_opts = get_yt_dlp_options(download_path, download_type, quality, progress_hook_wrapper)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'video')
            
            # Post-process based on type
            if download_type == "Comments":
                return process_comments(info_dict, download_path, video_title)
            elif download_type in ["Transcript", "Transcript (Plain Text)"]:
                return process_transcript(download_path, download_type)
            else:
                 return process_media(download_path)

    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def process_comments(info_dict, download_path, video_title):
    comments = info_dict.get('comments', [])
    if not comments:
         return {'status': 'warning', 'message': "No comments found or disabled."}

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
                'date': comment.get('timestamp'),
                'text': comment.get('text'),
                'likes': comment.get('like_count')
            })
    return {'status': 'success', 'file_path': csv_path}


def process_transcript(download_path, download_type):
    files = os.listdir(download_path)
    sub_files = [f for f in files if f.endswith('.vtt')]
    
    if not sub_files:
        return {'status': 'error', 'message': "No transcript found (en)."}
    
    vtt_path = os.path.join(download_path, sub_files[0])
    
    if download_type == "Transcript (Plain Text)":
        return convert_vtt_to_txt(vtt_path, download_path, sub_files[0])
    
    return {'status': 'success', 'file_path': vtt_path}


def convert_vtt_to_txt(vtt_path, download_path, filename):
    txt_filename = filename.replace('.vtt', '.txt')
    txt_path = os.path.join(download_path, txt_filename)
    
    unique_lines = []
    last_line = ""
    
    with open(vtt_path, 'r', encoding='utf-8') as f_vtt:
        for line in f_vtt:
            line = line.strip()
            if "WEBVTT" in line or "-->" in line or not line: continue
            if line.startswith("Kind:") or line.startswith("Language:"): continue
            if line.isdigit(): continue
            
            clean_line = re.sub(r'<[^>]+>', '', line).strip()
            if not clean_line: continue
            
            if clean_line != last_line:
                unique_lines.append(clean_line)
                last_line = clean_line
                
    with open(txt_path, 'w', encoding='utf-8') as f_txt:
        f_txt.write("\n".join(unique_lines))
        
    return {'status': 'success', 'file_path': txt_path}


def process_media(download_path):
    files = os.listdir(download_path)
    # Filter out transcript/csv files
    media_files = [f for f in files if not f.endswith('.vtt') and not f.endswith('.csv')]
    
    if media_files:
        return {'status': 'success', 'file_path': os.path.join(download_path, media_files[0])}
    
    return {'status': 'error', 'message': "Could not locate downloaded media file."}
