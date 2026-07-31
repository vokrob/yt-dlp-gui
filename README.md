<h1>
  <img src="logo.png?v=2" width="32" height="32" style="vertical-align: text-bottom; margin-right: 8px;" />
  yt-dlp GUI
</h1>

Paste a link, pick the quality, and download. No setup, everything updates itself.

## What it does

- Videos as MP4 (144p to 4K), audio as MP3, from YouTube and [hundreds of other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- Download queue that survives restarts; history with search and export (JSON/CSV)
- Reads cookies from Chrome, Edge, Firefox, Opera, Safari on its own, so age-restricted videos just work
- Updates yt-dlp, ffmpeg and itself automatically
- Speaks human: cryptic yt-dlp errors are translated
- Settings for proxy, speed limit, file names, subtitles, thumbnails
- Toast when a download finishes; Ctrl+V works on any keyboard layout

## Screenshots

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

## Install

1. Download the latest `.exe` from [Releases](../../releases) (~23 MB). Windows 10/11 (64-bit) only
2. Run it. It is unsigned, so SmartScreen may ask you to confirm: click "More info", then "Run anyway"
3. First launch downloads yt-dlp and ffmpeg (~130 MB, 1-2 minutes)

## Build from source

```bash
git clone https://github.com/vokrob/yt-dlp-gui.git
cd yt-dlp-gui
pip install -r requirements.txt
python main.py
```

To build the exe: `pip install pyinstaller` and `python build.py`. Releases are also built automatically on version tags via GitHub Actions.

## Settings and notes

- Settings live in `%APPDATA%\yt-dlp-gui\settings.json`; the settings window is all you need
- If browser cookies do not work, export them with the "Get cookies.txt" extension and put `cookies.txt` next to the exe
- YouTube may require a VPN in some regions
