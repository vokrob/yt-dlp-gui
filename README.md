<h1>
  <img src="logo.png?v=2" width="32" height="32" style="vertical-align: text-bottom; margin-right: 8px;" />
  <sup>yt-dlp GUI</sup>
</h1>

Paste a link, pick the quality, and download. No setup, everything updates itself.

## Description

Videos as MP4 (144p to 4K), audio as MP3, from YouTube and [hundreds of other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

- Queue that survives restarts; history with search and export (JSON/CSV)
- Cookies read automatically from installed browsers, so age-restricted videos just work
- Updates yt-dlp, ffmpeg and itself automatically

#### Screenshots

![URL Input](assets/url-input.png)
*Paste a link and press Enter*

---

![Video Preview](assets/video-preview.png)
*Choose your quality, format, and save location*

---

![Download Progress](assets/download-progress.png)
*Track your downloads*

## Tech Stack

- Python 3.9+
- CustomTkinter
- yt-dlp
- Pillow
- PyInstaller

## Installation

1. Download the latest `.exe` from [Releases](../../releases) (~23 MB). Windows 10/11 only
2. Run it. It is unsigned, so SmartScreen may ask you to confirm: click "More info", then "Run anyway"
3. First launch downloads yt-dlp and ffmpeg (~130 MB, 1-2 minutes)

Build from source:

```bash
git clone https://github.com/vokrob/yt-dlp-gui.git
cd yt-dlp-gui
pip install -r requirements.txt
python main.py
```

To build the exe: `pip install pyinstaller`, then `python build.py`. Releases are also built automatically on version tags.

## Usage

1. Launch the app and paste a video URL
2. Wait for the preview to load (title, duration, thumbnail, quality options)
3. Choose Video or Audio, pick the quality, press Start
4. Watch progress in the queue; pause or cancel anytime
5. History, statistics and settings are in the main window

- If browser cookies do not work, export them with the "Get cookies.txt" extension and put `cookies.txt` next to the exe
- YouTube may require a VPN in some regions
