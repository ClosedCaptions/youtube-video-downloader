#!/usr/bin/env python3
"""
YouTube Video Downloader

Asks for a YouTube URL and downloads the video to your computer.

Requirements:
    pip install yt-dlp

Optional (recommended): install FFmpeg so the best-quality video and audio
streams can be merged into one file. Without FFmpeg, the script downloads the
best single file that already contains both video and audio (often up to 720p).
    - Windows: winget install ffmpeg
    - macOS:   brew install ffmpeg
    - Linux:   sudo apt install ffmpeg

Usage:
    python youtube_downloader.py
    python youtube_downloader.py "https://www.youtube.com/watch?v=..."
    python youtube_downloader.py "https://www.youtube.com/watch?v=..." --audio
    python youtube_downloader.py "https://www.youtube.com/watch?v=..." --video --out "C:\\Videos"

    python youtube_downloader.py "https://www.youtube.com/playlist?list=..." --audio

Audio-only mode saves an MP3 (needs FFmpeg); without FFmpeg it saves M4A.
Playlists are saved into a subfolder named after the playlist, with files
numbered in playlist order. Use --single to ignore the playlist part of a link.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Install it with:\n    pip install yt-dlp")
    sys.exit(1)


def default_download_dir() -> Path:
    """Return ~/Downloads if it exists, otherwise the current folder."""
    downloads = Path.home() / "Downloads"
    return downloads if downloads.is_dir() else Path.cwd()


def is_youtube_url(url: str) -> bool:
    url = url.lower()
    return any(host in url for host in ("youtube.com/", "youtu.be/"))


def format_duration(seconds) -> str:
    """Format seconds (int or float, possibly None) as M:SS or H:MM:SS."""
    total = int(seconds or 0)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def playlist_kind(url: str) -> str | None:
    """Classify a URL: 'playlist' (a pure playlist page), 'video_in_playlist'
    (a video link that also carries a playlist id), or None (single video)."""
    parsed = urlparse(url)
    if parsed.path.startswith("/playlist"):
        return "playlist"
    if "list" in parse_qs(parsed.query):
        return "video_in_playlist"
    return None


_announced: set[str] = set()


def progress_hook(d: dict) -> None:
    info = d.get("info_dict") or {}
    index = info.get("playlist_index")
    if d["status"] == "downloading" and index and info.get("id") not in _announced:
        _announced.add(info.get("id"))
        print(f"\n[{index}/{info.get('n_entries') or '?'}] {info.get('title')}")
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        print(f"\r  Downloading: {percent}  at {speed}  ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print("\n  Download finished, processing...")


def find_ffmpeg() -> str | None:
    """Return the folder containing ffmpeg, or None if it can't be found.

    Checks PATH first, then the WinGet install location, so it still works in
    a terminal that was opened before FFmpeg was installed.
    """
    on_path = shutil.which("ffmpeg")
    if on_path:
        return str(Path(on_path).parent)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        packages = Path(local) / "Microsoft" / "WinGet" / "Packages"
        for exe in packages.glob("Gyan.FFmpeg*/**/bin/ffmpeg.exe"):
            return str(exe.parent)
    return None


def download_video(
    url: str, output_dir: Path, audio_only: bool = False, playlist: bool = False
) -> None:
    ffmpeg_dir = find_ffmpeg()
    has_ffmpeg = ffmpeg_dir is not None

    if audio_only:
        if has_ffmpeg:
            # Best audio stream, converted to MP3
            fmt = "bestaudio/best"
        else:
            print("  Note: FFmpeg not found - saving audio in its original format (M4A).")
            fmt = "bestaudio[ext=m4a]/bestaudio"
    elif has_ffmpeg:
        # Best video + best audio, merged into an MP4
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
    else:
        print("  Note: FFmpeg not found - downloading best single combined file.")
        fmt = "best[acodec!=none][vcodec!=none]/best"

    ydl_opts = {
        "format": fmt,
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "noplaylist": not playlist,  # single video unless a playlist was requested
        "progress_hooks": [progress_hook],
        "quiet": True,
        "noprogress": True,  # we print our own progress line
        "no_warnings": True,
    }
    if has_ffmpeg:
        ydl_opts["ffmpeg_location"] = ffmpeg_dir
        if audio_only:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            ydl_opts["merge_output_format"] = "mp4"

    # YouTube extraction needs a JavaScript runtime (deno is enabled by default;
    # enable node too if it's installed).
    if shutil.which("node") and not shutil.which("deno"):
        ydl_opts["js_runtimes"] = {"node": {}}

    if playlist:
        download_playlist(url, output_dir, ydl_opts)
        return

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # A pure playlist URL ignores noplaylist; require --playlist for those.
        if info.get("_type") == "playlist":
            print("  That's a playlist URL - re-run with --playlist to download it all.")
            return

        print(f"\n  Title:    {info.get('title')}")
        print(f"  Channel:  {info.get('uploader')}")
        print(f"  Duration: {format_duration(info.get('duration'))}\n")

        # Reuse the info we already fetched instead of extracting it again
        ydl.process_ie_result(info, download=True)

    print(f"\n✔ Saved to: {output_dir}")


def download_playlist(url: str, output_dir: Path, ydl_opts: dict) -> None:
    """Download every video in a playlist into <output_dir>/<playlist title>/."""
    # Quick listing (no per-video lookups) so we can show what's coming.
    listing_opts = {k: ydl_opts[k] for k in ("js_runtimes",) if k in ydl_opts}
    listing_opts.update(extract_flat="in_playlist", quiet=True, no_warnings=True)
    with yt_dlp.YoutubeDL(listing_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = [e for e in (info.get("entries") or []) if e]
    if not entries:
        print("  No videos found in that playlist (is it private or empty?).")
        return
    print(f"\n  Playlist: {info.get('title')}")
    print(f"  Videos:   {len(entries)}")

    opts = dict(ydl_opts)
    opts["noplaylist"] = False
    opts["ignoreerrors"] = True  # skip private/deleted videos instead of stopping
    opts["outtmpl"] = str(
        output_dir / "%(playlist_title)s" / "%(playlist_index)03d - %(title)s.%(ext)s"
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        had_errors = ydl.download([url])

    print(f"\n✔ Saved to: {output_dir / (info.get('title') or '')}")
    if had_errors:
        print("  Note: some videos were skipped (private, deleted or unavailable).")


def main() -> None:
    print("=== YouTube Video Downloader ===\n")

    try:
        parser = argparse.ArgumentParser(description="Download a YouTube video or its audio.")
        parser.add_argument("url", nargs="?", help="YouTube video URL")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--audio", action="store_true", help="download audio only (MP3)")
        mode.add_argument("--video", action="store_true", help="download video (skip the prompt)")
        parser.add_argument("--out", help="folder to save into (skip the prompt)")
        scope = parser.add_mutually_exclusive_group()
        scope.add_argument("--playlist", action="store_true",
                           help="download every video in the playlist")
        scope.add_argument("--single", action="store_true",
                           help="download only the one video, even if the link has a playlist")
        opts = parser.parse_args()
        audio_flag = opts.audio

        url = (opts.url or input("Enter YouTube URL: ")).strip()
        if not url:
            print("No URL entered. Exiting.")
            return
        if not is_youtube_url(url):
            print("That doesn't look like a YouTube URL.")
            return

        kind = playlist_kind(url)
        if opts.playlist:
            playlist = True
        elif kind == "playlist":
            if opts.single:
                print("That link is a playlist, not a single video; drop --single.")
                return
            playlist = True
        elif kind == "video_in_playlist" and not opts.single:
            choice = input("This video is part of a playlist. Download only "
                           "[t]his video or the [w]hole playlist? [t]: ").strip().lower()
            playlist = choice.startswith("w")
        else:
            playlist = False

        if audio_flag or opts.video:
            audio_only = audio_flag
        else:
            choice = input("Download [v]ideo or [a]udio only? [v]: ").strip().lower()
            audio_only = choice.startswith("a")

        default_dir = default_download_dir()
        folder = opts.out or input(f"Save to folder [{default_dir}]: ").strip()
        output_dir = Path(folder).expanduser() if folder else default_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        download_video(url, output_dir, audio_only, playlist)
    except yt_dlp.utils.DownloadError as e:
        print(f"\n✘ Download failed: {e}")
        if "format is not available" in str(e) and not find_ffmpeg():
            print("  YouTube now serves video and audio separately, so FFmpeg is required.")
            print("  Install it with:  winget install Gyan.FFmpeg   (then open a new terminal)")
        else:
            print("  Tip: try updating yt-dlp with:  pip install -U yt-dlp")
    except OSError as e:
        print(f"\n✘ File/folder error: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")


if __name__ == "__main__":
    main()
