<h1>
  <img src="assets/logo.png?v=2" width="32" height="32" style="vertical-align: text-bottom; margin-right: 8px;" />
  <sup>yt-dlp GUI</sup>
</h1>

<video src="https://github.com/user-attachments/assets/f9489d07-ffb4-4aec-9a5b-c60e66b7c76d"></video>

Paste a link, pick the quality, and download. No setup, everything updates itself

## Description

Videos as MP4 (144p to 8K), audio as MP3, from YouTube and [hundreds of other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

- Queue that survives restarts
- Cookies read automatically from installed browsers, so age-restricted videos just work
- Updates yt-dlp and itself automatically

## Tech Stack

- Python 3.9+
- CustomTkinter
- yt-dlp
- requests
- packaging
- Pillow
- PyInstaller

## Installation

1. Download the latest `.exe` from [Releases](../../releases). Windows 10/11 only
2. Run it. It is unsigned, so SmartScreen may ask you to confirm: click "More info", then "Run anyway"
3. First launch downloads yt-dlp and ffmpeg

### Build from source

```bash
git clone https://github.com/vokrob/yt-dlp-gui.git
cd yt-dlp-gui
pip install -r requirements.txt
python main.py
```

To build the exe: `pip install pyinstaller`, then `python build.py`.

## Usage

1. Launch the app and paste a video URL
2. Wait for the preview to load (title, thumbnail, quality options)
3. Choose Video or Audio, pick the quality and save location, press Start
4. Watch progress in the queue

- If browser cookies do not work, export them with the "Get cookies.txt" extension and put `cookies.txt` next to the exe
- YouTube may require a VPN in some regions


