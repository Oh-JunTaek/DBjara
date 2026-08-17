"""
Auto-updater module for DBjara
Checks GitHub Releases API for new versions and downloads updates.
"""

import json
import urllib.request
import urllib.error
import webbrowser
from typing import Tuple, Optional

CURRENT_VERSION = "v1.0.0"
GITHUB_REPO = "Oh-JunTaek/DBjara"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_latest_version_info() -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Check GitHub Releases for the latest version.
    Returns (has_update, latest_version_tag, release_notes, download_url)
    """
    req = urllib.request.Request(
        RELEASES_API_URL,
        headers={"User-Agent": "DBjara-Updater", "Accept": "application/vnd.github.v3+json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.getcode() == 200:
                data = json.loads(resp.read().decode("utf-8"))
                latest_tag = data.get("tag_name", "")
                body = data.get("body", "")
                html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")

                # Find .exe asset if available
                download_url = html_url
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url", html_url)
                        break

                if latest_tag and latest_tag != CURRENT_VERSION:
                    return True, latest_tag, body, download_url
                return False, CURRENT_VERSION, body, download_url
    except Exception as e:
        print(f"[Updater] Error checking for updates: {e}")

    return False, CURRENT_VERSION, None, None


def open_release_page(url: Optional[str] = None):
    """Open the GitHub release download page in the default web browser."""
    target_url = url or f"https://github.com/{GITHUB_REPO}/releases/latest"
    webbrowser.open(target_url)


if __name__ == "__main__":
    has_update, tag, body, url = get_latest_version_info()
    print(f"Current: {CURRENT_VERSION}, Latest: {tag}, Has Update: {has_update}")
    print(f"Download URL: {url}")
