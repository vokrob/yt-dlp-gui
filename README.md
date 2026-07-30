<h1>
  <img src="logo.png?v=2" width="32" height="32" style="vertical-align: text-bottom; margin-right: 8px;" />
  yt-dlp GUI
</h1>

## Description

A modern desktop GUI for downloading videos and audio from [hundreds of sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) using yt-dlp. Binaries (yt-dlp, ffmpeg) are downloaded automatically on first launch — no manual setup required.

**Features:**
- Downloads video as MP4 (144p to 4K) and audio as MP3
- Download queue with persistence across restarts
- Download history with search, statistics, and export (JSON/CSV)
- Auto-extracts cookies from Chrome, Firefox, Edge, Opera, Safari
- Auto-updates yt-dlp and ffmpeg on each launch
- Self-updates the GUI itself via GitHub releases
- User-friendly error messages (translates cryptic yt-dlp errors)
- Settings: proxy, rate limiting, filename templates, subtitles, thumbnails
- Toast notifications on download complete
- Smart paste (Ctrl+V works on any keyboard layout, including Russian)

### Screenshots

#### URL Input
![URL Input](assets/url-input.png)
*Just paste a link and hit enter*

---

#### Video Preview
![Video Preview](assets/video-preview.png)
*Pick your quality and format*

---

#### Download Progress
![Download Progress](assets/download-progress.png)
*Watch your downloads in the queue*

## Tech Stack

- **Python 3.9+** — Core language
- **CustomTkinter** — Modern GUI framework
- **yt-dlp** (standalone binary) — Download engine, downloaded at first run
- **Pillow** — Image processing
- **PyInstaller** — Executable builds

## Installation

### Pre-built executable
1. Download the latest `.exe` from [Releases](../../releases) (~18 MB)
2. Run `yt-dlp-gui.exe`
3. On first launch, yt-dlp and ffmpeg binaries (~50 MB) are downloaded automatically

### From source
```bash
git clone https://github.com/vokrob/yt-dlp-gui.git
cd yt-dlp-gui
pip install -r requirements.txt
python main.py
```

### Build executable
```bash
pip install pyinstaller
python build.py
```

Builds are also automated via GitHub Actions — pushes of version tags trigger a workflow that produces the `.exe` artifact.

## Usage

1. Launch the application
2. Paste a video URL (Ctrl+V works on any keyboard layout)
3. Wait for the video preview to load (title, duration, thumbnail, quality options)
4. Choose **Video** or **Audio** mode, then select desired quality
5. Click **Start** to begin downloading
6. Downloads appear in the queue — monitor progress, pause, or cancel
7. Access your download history and settings from the main window

## Configuration

Settings are stored in `%APPDATA%\yt-dlp-gui\settings.json`. Configure via the GUI settings panel — no manual file editing required.

