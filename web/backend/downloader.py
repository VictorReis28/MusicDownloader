import os
import asyncio
from typing import Callable, Optional
from yt_dlp import YoutubeDL
from static_ffmpeg import run

# Configure FFmpeg
ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
FFMPEG_PATH = os.path.dirname(ffmpeg_path)

INVALID_CHARS = '"<>:/\\|?*\n\r\t'

def sanitize_filename(name: str) -> str:
    for ch in INVALID_CHARS:
        name = name.replace(ch, '_')
    name = name.strip()
    if len(name) > 200:
        name = name[:200].rstrip()
    return name

class Downloader:
    def __init__(self, progress_callback: Optional[Callable] = None, loop=None):
        self.progress_callback = progress_callback
        self.loop = loop or asyncio.get_event_loop()
        self.current_video = None
        self.current_index = 1
        self.total_videos = 1

    def _progress_hook(self, d):
        if self.progress_callback:
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('%', '').strip()
                try:
                    percent = float(p)
                except:
                    percent = 0
                
                asyncio.run_coroutine_threadsafe(
                    self.progress_callback({
                        "status": "downloading",
                        "percent": percent,
                        "title": self.current_video,
                        "index": self.current_index,
                        "total": self.total_videos,
                        "speed": d.get('_speed_str', 'N/A'),
                        "eta": d.get('_eta_str', 'N/A')
                    }),
                    self.loop
                )
            elif d['status'] == 'finished':
                asyncio.run_coroutine_threadsafe(
                    self.progress_callback({
                        "status": "finished",
                        "percent": 100,
                        "title": self.current_video,
                        "index": self.current_index,
                        "total": self.total_videos
                    }),
                    self.loop
                )

    async def get_info(self, url: str):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
        }
        with YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

    async def download(self, url: str, out_dir: str, format_type: str = 'mp3', quality: str = '192'):
        os.makedirs(out_dir, exist_ok=True)
        
        info = await self.get_info(url)
        
        if 'entries' in info:
            entries = [e for e in info['entries'] if e]
            self.total_videos = len(entries)
            for idx, entry in enumerate(entries, 1):
                self.current_index = idx
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}"
                video_title = entry.get('title') or f"Video {idx}"
                self.current_video = video_title
                
                await self._download_single(video_url, out_dir, format_type, quality, video_title)
        else:
            self.total_videos = 1
            self.current_index = 1
            self.current_video = info.get('title', 'video')
            await self._download_single(url, out_dir, format_type, quality, self.current_video)

    async def _download_single(self, url: str, out_dir: str, format_type: str, quality: str, title: str):
        safe_title = sanitize_filename(title)
        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        final_path = os.path.join(out_dir, f"{safe_title}.{ext}")

        ydl_opts = {
            'noplaylist': True,
            'progress_hooks': [self._progress_hook],
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': FFMPEG_PATH,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
        }

        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(out_dir, f"{safe_title}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        else:
            # mp4
            q = quality if quality != 'best' else '1080'
            ydl_opts.update({
                'format': f'bestvideo[height<={q}]+bestaudio/best/best',
                'outtmpl': os.path.join(out_dir, f"{safe_title}.%(ext)s"),
                'merge_output_format': 'mp4',
            })

        with YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ydl.download([url]))
