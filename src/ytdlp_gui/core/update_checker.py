"""
Update Checker - Check GitHub releases and self-update
"""

import os
import sys
import json
import logging
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict
from packaging.version import Version, InvalidVersion

import requests

from ytdlp_gui import __version__

GITHUB_REPO = "vokrob/yt-dlp-gui"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


CACHE_TTL = 6 * 3600  # 6 hours between update checks


class UpdateChecker:
    """Check for updates and apply them"""

    def __init__(self, settings_manager=None):
        self.logger = logging.getLogger(__name__)
        self._current_version = self._parse_version(__version__)
        self._settings = settings_manager

    def _parse_version(self, version_str: str) -> Optional[Version]:
        try:
            return Version(version_str)
        except InvalidVersion:
            return None

    def is_frozen(self) -> bool:
        return getattr(sys, 'frozen', False)

    def _load_cache(self) -> Optional[Dict]:
        """Load cached update info from settings"""
        if not self._settings:
            return None
        try:
            last_check = self._settings.get('last_update_check_time', 0.0)
            elapsed = __import__('time').time() - last_check
            if elapsed < CACHE_TTL:
                cached = self._settings.get('latest_update_info', '')
                if cached:
                    return json.loads(cached)
        except Exception as e:
            self.logger.warning(f"Failed to load update cache: {e}")
        return None

    def _save_cache(self, info: dict):
        """Save update info to settings cache"""
        if not self._settings:
            return
        try:
            import time
            self._settings.set('last_update_check_time', time.time())
            self._settings.set('latest_available_version', info.get('latest_version', ''))
            self._settings.set('latest_update_info', json.dumps(info))
        except Exception as e:
            self.logger.warning(f"Failed to save update cache: {e}")

    def check(self) -> Optional[Dict]:
        """Check GitHub for latest release. Uses cached result if fresh."""
        cached = self._load_cache()
        if cached is not None:
            self.logger.info("Using cached update check result")
            return cached

        try:
            resp = requests.get(
                GITHUB_API,
                timeout=10,
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()

            tag = data.get("tag_name", "")
            latest_version = self._parse_version(tag.lstrip("v"))

            if not latest_version:
                self.logger.warning(f"Could not parse latest version tag: {tag}")
                return None

            result = {
                "available": False,
                "current_version": __version__,
                "latest_version": tag.lstrip("v"),
                "release_notes": data.get("body", ""),
                "release_url": data.get("html_url", ""),
            }

            if self._current_version and latest_version > self._current_version:
                asset_url = self._find_asset(data)
                if not asset_url:
                    self.logger.warning("No matching asset found for this platform")
                    self._save_cache(result)
                    return result

                result["available"] = True
                result["download_url"] = asset_url

            self._save_cache(result)
            return result

        except requests.RequestException as e:
            self.logger.warning(f"Failed to check for updates: {e}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to parse update response: {e}")
            return None

    def _find_asset(self, release_data: dict) -> Optional[str]:
        """Find the download URL for the current platform"""
        system = platform.system()

        if system == "Windows":
            suffix = "windows-amd64.exe"
        elif system == "Darwin":
            suffix = "macos-amd64"
        elif system == "Linux":
            suffix = "linux-amd64"
        else:
            return None

        for asset in release_data.get("assets", []):
            name = asset.get("name", "")
            if name.endswith(suffix):
                return asset.get("browser_download_url")

        return None

    def download_update(
        self, url: str, dest_dir: str,
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """Download executable directly. Returns path to exe."""
        os.makedirs(dest_dir, exist_ok=True)

        system = platform.system()
        exe_name = "yt-dlp-gui.exe" if system == "Windows" else "yt-dlp-gui"
        exe_path = os.path.join(dest_dir, exe_name)

        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()

            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(exe_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded / total_size)

            if system != "Windows":
                os.chmod(exe_path, 0o755)

            return exe_path

        except Exception as e:
            self.logger.error(f"Failed to download update: {e}")
            return None

    def apply_update(self, new_exe_path: str) -> None:
        """Replace old executable with new one and restart"""
        if not self.is_frozen():
            self.logger.warning("Not a frozen executable, cannot self-update")
            return

        old_exe = sys.executable
        parent_pid = os.getpid()
        update_dir = os.path.dirname(new_exe_path)

        system = platform.system()
        if system == "Windows":
            self._apply_windows(new_exe_path, old_exe, parent_pid, update_dir)
        else:
            self._apply_unix(new_exe_path, old_exe, parent_pid, update_dir)

    def _apply_windows(self, new_exe: str, old_exe: str, parent_pid: int, update_dir: str):
        ps_script = (
            f"$parent = {parent_pid}\n"
            f'$new = "{new_exe}"\n'
            f'$old = "{old_exe}"\n'
            f'$dir = "{update_dir}"\n'
            "while (Get-Process -Id $parent -ErrorAction SilentlyContinue) {\n"
            "    Start-Sleep -Milliseconds 500\n"
            "}\n"
            "Start-Sleep -Seconds 1\n"
            "try {\n"
            "    Copy-Item -Path $new -Destination $old -Force\n"
            "    Start-Process $old\n"
            "    Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue\n"
            "} catch {\n"
            "    Write-Error $_\n"
            "    Start-Sleep -Seconds 5\n"
            "}\n"
        )
        ps_file = os.path.join(update_dir, "updater.ps1")
        with open(ps_file, "w") as f:
            f.write(ps_script)

        subprocess.Popen([
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", ps_file
        ])

    def _apply_unix(self, new_exe: str, old_exe: str, parent_pid: int, update_dir: str):
        sh_script = (
            "#!/bin/bash\n"
            f"parent={parent_pid}\n"
            f'new="{new_exe}"\n'
            f'old="{old_exe}"\n'
            f'dir="{update_dir}"\n'
            "while kill -0 $parent 2>/dev/null; do sleep 1; done\n"
            "sleep 1\n"
            'cp "$new" "$old"\n'
            'chmod +x "$old"\n'
            '"$old" &\n'
            'rm -rf "$dir"\n'
        )
        sh_file = os.path.join(update_dir, "updater.sh")
        with open(sh_file, "w") as f:
            f.write(sh_script)
        os.chmod(sh_file, 0o755)
        subprocess.Popen(["bash", sh_file], start_new_session=True)
