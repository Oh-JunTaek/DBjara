"""
DBjara - 자동 업데이트 확인 모듈
GitHub Releases API를 조회하여 최신 버전 확인 및 다운로드 페이지 연결을 처리합니다.
"""

import json
import urllib.request
import urllib.error
import webbrowser
from typing import Tuple, Optional

# 현재 프로그램 버전
CURRENT_VERSION = "v1.0.0"
GITHUB_REPO = "Oh-JunTaek/DBjara"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_latest_version_info() -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    GitHub Releases에서 최신 버전 정보를 조회합니다.
    반환값: (업데이트_존재_여부, 최신_버전_태그, 릴리즈_노트, 다운로드_URL)
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

                # 배포된 .exe 파일이 있는 경우 해당 다운로드 링크 추출
                download_url = html_url
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url", html_url)
                        break

                if latest_tag and latest_tag != CURRENT_VERSION:
                    return True, latest_tag, body, download_url
                return False, CURRENT_VERSION, body, download_url
    except Exception as e:
        print(f"[Updater] 업데이트 확인 중 오류 발생: {e}")

    return False, CURRENT_VERSION, None, None


def open_release_page(url: Optional[str] = None):
    """기본 웹 브라우저에서 GitHub 최신 릴리즈 다운로드 페이지를 엽니다."""
    target_url = url or f"https://github.com/{GITHUB_REPO}/releases/latest"
    webbrowser.open(target_url)


if __name__ == "__main__":
    has_update, tag, body, url = get_latest_version_info()
    print(f"현재 버전: {CURRENT_VERSION}, 최신 버전: {tag}, 업데이트 필요: {has_update}")
    print(f"다운로드 URL: {url}")
