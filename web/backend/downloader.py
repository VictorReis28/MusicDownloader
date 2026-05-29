import os
import asyncio
from typing import Callable, Optional
from yt_dlp import YoutubeDL
from static_ffmpeg import run

# Configure FFmpeg
ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
FFMPEG_PATH = os.path.dirname(ffmpeg_path)

INVALID_CHARS = '"<>:/\\|?*\n\r\t'
VALID_MP3_QUALITIES = {'128', '192', '256', '320'}
VALID_MP4_QUALITIES = {'144', '240', '360', '480', '720', '1080', 'best'}

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

    async def _emit_error(self, message: str):
        if self.progress_callback:
            await self.progress_callback({
                "status": "error",
                "percent": 0,
                "title": self.current_video or "video",
                "index": self.current_index,
                "total": self.total_videos,
                "message": message,
            })

    def _validate_quality(self, format_type: str, quality: str):
        if format_type == 'mp3' and quality not in VALID_MP3_QUALITIES:
            raise ValueError(f"Qualidade de audio invalida: {quality}.")
        if format_type == 'mp4' and quality not in VALID_MP4_QUALITIES:
            raise ValueError(f"Qualidade de video invalida: {quality}.")

    async def _assert_exact_video_quality_available(self, url: str, quality: str):
        if quality == 'best':
            return

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
        }

        with YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

        available_heights = sorted({
            f.get('height')
            for f in info.get('formats', [])
            if f.get('vcodec') != 'none' and f.get('height')
        })

        requested_height = int(quality)
        if requested_height not in available_heights:
            options = ', '.join(f"{h}p" for h in available_heights) if available_heights else 'nenhuma'
            raise ValueError(
                f"A qualidade {quality}p nao esta disponivel para este video. Disponiveis: {options}."
            )

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

        try:
            self._validate_quality(format_type, quality)
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
        except Exception as e:
            await self._emit_error(str(e))
            raise

    async def _download_single(self, url: str, out_dir: str, format_type: str, quality: str, title: str):
        safe_title = sanitize_filename(title)
        ext = 'mp3' if format_type == 'mp3' else 'mp4'

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
                'prefer_ffmpeg': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'postprocessor_args': ['-b:a', f'{quality}k'],
            })
        else:
            # mp4
            await self._assert_exact_video_quality_available(url, quality)
            if quality == 'best':
                format_selector = 'bestvideo+bestaudio/best'
            else:
                format_selector = (
                    f'bestvideo[height={quality}][ext=mp4]+bestaudio[ext=m4a]/'
                    f'best[height={quality}][ext=mp4]/'
                    f'bestvideo[height={quality}]+bestaudio/'
                    f'best[height={quality}]'
                )
            ydl_opts.update({
                'format': format_selector,
                'outtmpl': os.path.join(out_dir, f"{safe_title}.%(ext)s"),
                'merge_output_format': 'mp4',
            })

        with YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ydl.download([url]))
