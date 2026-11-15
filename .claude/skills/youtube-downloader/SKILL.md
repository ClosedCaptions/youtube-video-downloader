---
name: youtube-downloader
description: Download a YouTube video (MP4), just its audio (MP3), or a whole playlist of either, to the user's computer using yt-dlp. Use when the user gives a YouTube video or playlist URL and asks to download, save, grab, or rip videos or audio.
---

# YouTube downloader

Wraps `scripts/youtube_downloader.py` (yt-dlp). Only download content the user has the right to save (their own, Creative Commons, or permitted by the uploader).

## Run

Always pass the URL and `--out` so the script never waits on a prompt. Quote the URL.

```
python "<this skill dir>/scripts/youtube_downloader.py" "<URL>" --video --out "<folder>"
python "<this skill dir>/scripts/youtube_downloader.py" "<URL>" --audio --out "<folder>"
```

- `--video` saves an MP4, `--audio` saves an MP3 (192 kbps). Pick from the user's request; if unclear, ask.
- `--out` defaults to asking; use the user's folder, or `%USERPROFILE%\Downloads` if they didn't say.
- Playlists: add `--playlist` to download every video (into `<out>/<playlist title>/`, numbered in order, works with `--audio` too). A `playlist?list=` link is treated as a playlist automatically. For a watch link that also has `&list=`, pass `--playlist` or `--single` (otherwise the script prompts). Private/deleted videos are skipped. Large playlists take a while; tell the user how many videos it contains first if asked to confirm.

## Requirements

- `pip install yt-dlp` (if missing, install it; run `pip install -U yt-dlp` if downloads fail).
- FFmpeg is needed for video+audio merging and MP3 conversion: `winget install Gyan.FFmpeg`. The script finds the WinGet install even if the terminal PATH is stale.
- Node or Deno is used as the JavaScript runtime YouTube extraction needs (Node is auto-enabled).

## Troubleshooting

- "Requested format is not available" with no FFmpeg: install FFmpeg.
- Other failures: update yt-dlp. Age-restricted, private, or members-only videos are not supported (no cookies option).
- Report the saved file's name and folder to the user when done.
