"""
DBjara - 설정 관리 및 약정 기간 / 규칙 영구 보관 모듈
"""

import os
import json
import winreg
import sys
from datetime import datetime, timedelta
from i18n import set_language

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DBjara"

# DBjara 기본 설정값 정의
DEFAULT_CONFIG = {
    "language": "ko",
    # 약정 기간 설정 ("none", "1day", "7days", "30days")
    "commitment_plan": "none",
    "commitment_end_date": "",  # e.g. "2026-08-31 23:59:59"
    # 1인 솔로 플레이 제어 ("block_always", "time_limit", "unlimited")
    "solo_rule": "block_always",
    "solo_limit_minutes": 60,
    # 2인 이상 다인큐(파티) 제어 ("unlimited", "time_limit", "block_always")
    "party_rule": "time_limit",
    "party_limit_minutes": 120,
    # 야간 강제 취침 모드
    "night_lock": True,
    "night_start": "23:00",
    "night_end": "07:00",
    # 스마트 멘탈 쿨다운 (게임 후 5분 휴식)
    "cooldown_enabled": True,
    # 자제력 자물쇠 및 보안
    "otp_enabled": False,
    "otp_secret": "",
    # 당일 누적 시간 (초 단위)
    "daily_played_date": datetime.now().strftime("%Y-%m-%d"),
    "daily_solo_played_seconds": 0,
    "daily_party_played_seconds": 0,
    # 부팅 시 자동 실행
    "auto_start": False,
    # 부가 기능 및 전적/통계 수집
    "riot_id": "",
    "riot_api_key": "",
    "telemetry_enabled": True,
    "telemetry_uuid": "",
    "auto_update_check": True,
}


def load_config() -> dict:
    """config.json 파일에서 설정을 로드하고 날짜 변경 시 일일 누적 시간을 초기화합니다."""
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] 설정 파일 로드 오류 ({CONFIG_FILE}): {e}")

    # 언어 설정 반영
    set_language(config.get("language", "ko"))

    # 날짜가 바뀌었을 경우 당일 누적 시간 초기화
    today = datetime.now().strftime("%Y-%m-%d")
    if config.get("daily_played_date") != today:
        config["daily_played_date"] = today
        config["daily_solo_played_seconds"] = 0
        config["daily_party_played_seconds"] = 0
        save_config(config)

    # 약정 기간이 만료되었는지 확인
    end_date_str = config.get("commitment_end_date", "")
    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > end_dt:
                # 약정 종료 ➔ 자유 모드로 전환
                config["commitment_plan"] = "none"
                config["commitment_end_date"] = ""
                save_config(config)
        except Exception:
            pass

    return config


def calculate_commitment_end_date(plan: str) -> str:
    """선택한 약정 플랜에 따른 종료 일시를 반환합니다."""
    now = datetime.now()
    if plan == "1day":
        end_dt = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return end_dt.strftime("%Y-%m-%d %H:%M:%S")
    elif plan == "7days":
        end_dt = (now + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=0)
        return end_dt.strftime("%Y-%m-%d %H:%M:%S")
    elif plan == "30days":
        end_dt = (now + timedelta(days=29)).replace(hour=23, minute=59, second=59, microsecond=0)
        return end_dt.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def is_commitment_locked(config: dict) -> bool:
    """현재 유효한 약정 잠금 기간 내에 있는지 확인합니다."""
    end_date_str = config.get("commitment_end_date", "")
    if not end_date_str:
        return False
    try:
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        return datetime.now() <= end_dt
    except Exception:
        return False


def get_remaining_days(config: dict) -> int:
    """약정 기간의 남은 일수를 계산합니다."""
    end_date_str = config.get("commitment_end_date", "")
    if not end_date_str:
        return 0
    try:
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        delta = end_dt.date() - datetime.now().date()
        return max(0, delta.days)
    except Exception:
        return 0


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
