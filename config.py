"""
DBjara - 설정 관리 및 윈도우 시작 프로그램 연동 모듈
"""

import os
import json
import winreg
import sys
from datetime import datetime
from i18n import set_language

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DBjara"

# 기본 설정값 정의
DEFAULT_CONFIG = {
    "language": "ko",  # 표시 언어 ("ko": 한국어, "en": English)
    "mode": "medium",  # 통제 모드: "high"(전체 차단), "medium"(솔로 차단), "low"(시간 제한)
    "daily_limit_minutes": 120,  # '하' 모드 시 일일 최대 허용 솔로 시간(분)
    "night_lock": True,  # 야간 강제 차단 활성화 여부
    "night_start": "23:00",  # 야간 차단 시작 시각
    "night_end": "07:00",  # 야간 차단 종료 시각
    "otp_enabled": False,  # 동반자 OTP 인증 활성화 여부
    "otp_secret": "",  # 동반자 OTP 비밀키
    "daily_played_date": datetime.now().strftime("%Y-%m-%d"),  # 플레이 누적 기준 일자
    "daily_played_seconds": 0,  # 당일 솔로 플레이 누적 시간(초)
    "auto_start": False,  # 윈도우 부팅 시 자동 실행 여부
    "riot_id": "",  # 소환사 Riot ID (예: "소환사명#KR1")
    "riot_api_key": "",  # 라이엇 개발자 API 키 (선택 사항)
    "telemetry_enabled": True,  # 익명 사용 통계 전송 동의 여부
    "telemetry_uuid": "",  # 익명 기기 식별자
    "auto_update_check": True,  # 시작 시 자동 업데이트 확인 여부
}


def load_config() -> dict:
    """config.json 파일에서 설정을 불러옵니다. 파일이 없으면 기본값을 생성합니다."""
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] 설정 파일 읽기 실패 ({CONFIG_FILE}): {e}")

    # 언어 설정 반영
    set_language(config.get("language", "ko"))

    # 날짜가 바뀌었을 경우 당일 누적 플레이 시간 초기화
    today = datetime.now().strftime("%Y-%m-%d")
    if config.get("daily_played_date") != today:
        config["daily_played_date"] = today
        config["daily_played_seconds"] = 0
        save_config(config)

    return config


def save_config(config: dict) -> bool:
    """현재 설정을 config.json 파일에 저장합니다."""
    try:
        set_language(config.get("language", "ko"))
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Config] 설정 파일 저장 실패 ({CONFIG_FILE}): {e}")
        return False


def set_auto_start(enabled: bool) -> bool:
    """윈도우 시작 프로그램 레지스트리에 프로그램을 등록하거나 해제합니다."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_ALL_ACCESS
        )
        if enabled:
            python_exe = sys.executable
            app_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "app.py"
            )
            # 백그라운드 무창 실행을 위해 pythonw.exe 우선 사용
            pythonw_exe = os.path.join(
                os.path.dirname(python_exe), "pythonw.exe"
            )
            exe_to_use = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
            cmd = f'"{exe_to_use}" "{app_script}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Config] 자동 실행 설정 실패: {e}")
        return False
