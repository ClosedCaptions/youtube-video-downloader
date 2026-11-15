# YouTube Video Downloader

A small command-line tool that downloads a YouTube video (MP4) or just its audio (MP3) to your computer, built on [yt-dlp](https://github.com/yt-dlp/yt-dlp).

> Only download content you have the right to save, such as your own videos, Creative Commons videos, or ones the uploader permits. Downloading other videos may violate YouTube's Terms of Service.

## Features

- Download a video as MP4 at the best available quality
- Audio-only mode that saves an MP3 (192 kbps)
- Shows title, channel and duration before downloading
- Live progress with speed and ETA
- Finds FFmpeg automatically, even if your terminal's PATH is out of date (WinGet installs)
- Downloads whole playlists (video or audio only) into a numbered subfolder, skipping private or deleted videos
- Asks before downloading a whole playlist when a video link also belongs to one

## Requirements

| Requirement | Needed for | Install |
|---|---|---|
| Python 3.10+ (3.11+ recommended) | Running the script | [python.org](https://www.python.org/downloads/) |
| yt-dlp | Downloading | `pip install yt-dlp` |
| FFmpeg | Merging video + audio, MP3 conversion | Windows: `winget install Gyan.FFmpeg`<br>macOS: `brew install ffmpeg`<br>Linux: `sudo apt install ffmpeg` |
| Node.js or Deno | JavaScript runtime YouTube extraction needs | `winget install OpenJS.NodeJS` or `winget install DenoLand.Deno` |

YouTube now serves video and audio as separate streams, so **FFmpeg is effectively required**. Without it most downloads fail with `Requested format is not available`. (If only FFmpeg is missing, audio mode still works and saves M4A instead of MP3.)

## Usage

Interactive: the script asks for the URL, video or audio, and the save folder.

```
python youtube_downloader.py
```

With arguments:

```
python youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
python youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --audio
python youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --video --out "C:\Videos"
```

Playlists:

```
python youtube_downloader.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"
python youtube_downloader.py "https://www.youtube.com/playlist?list=PLAYLIST_ID" --audio --out "C:\Music"
```

A `playlist?list=` link is downloaded as a playlist automatically. If a normal video link also contains `&list=...`, the script asks whether you want just that video or the whole playlist (use `--playlist` or `--single` to skip the question). Files go into `<folder>/<playlist title>/` named `001 - Title.mp4`, `002 - Title.mp4`, and so on. Large playlists can take a long time and a lot of disk space.

Keep the quotes around the URL: in PowerShell an unquoted `&` breaks the command.

### Options

| Option | Description |
|---|---|
| `url` | YouTube video URL (prompted for if omitted) |
| `--audio` | Download audio only, saved as MP3 |
| `--video` | Download video, skipping the video/audio prompt |
| `--playlist` | Download every video in the playlist |
| `--single` | Download only the one video, even if the link also has a playlist |
| `--out FOLDER` | Folder to save into, skipping the folder prompt. Defaults to your Downloads folder |

Files are named `<video title>.<ext>`.

## Use as a Claude Code skill

The tool is also packaged as a Claude Code skill at `~/.claude/skills/youtube-downloader/`. In a new Claude Code session, ask for example "download this video: <URL>" or "get the audio from <URL>", or run `/youtube-downloader`.

The skill keeps its own copy of the script (`scripts/youtube_downloader.py`). If you change the script in this project, copy it there too.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Requested format is not available` | Install FFmpeg (see above). |
| `ffmpeg` not recognized in a new terminal | Restart your terminal or VS Code. The script also looks in the WinGet install folder on its own. |
| Download fails or only low-quality formats appear | Run `pip install -U yt-dlp`, and make sure Node.js or Deno is installed. |
| "term is not recognized" in PowerShell after an error | The URL was pasted at the shell prompt. Run `python youtube_downloader.py`, then paste the URL when asked. |
| "re-run with --playlist" | The link points to a playlist. Add `--playlist` to download it all. |
| Some playlist videos are missing | Private, deleted or region-locked videos are skipped; the script prints a note. |
| Age-restricted, private or members-only videos fail | Not supported. The script doesn't use browser cookies. |

## Project layout

```
youtube_downloader.py   the downloader (single file)
README.md               this file
```
