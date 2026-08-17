"""
Configuration and Persistence Manager for DBjara
"""

import os
import json
import winreg
import sys
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DBjara"

DEFAULT_CONFIG = {
    "mode": "medium",  # "high", "medium", "low"
    "daily_limit_minutes": 120,  # 'low' mode daily maximum solo minutes
    "night_lock": True,  # Night forced block
    "night_start": "23:00",
    "night_end": "07:00",
    "otp_enabled": False,  # Whether companion OTP verification is required
    "otp_secret": "",
    "daily_played_date": datetime.now().strftime("%Y-%m-%d"),
    "daily_played_seconds": 0,
    "auto_start": False,
    # New features
    "riot_id": "",  # e.g. "Hide on bush#KR1"
    "riot_api_key": "",  # Optional Riot Developer API key
    "telemetry_enabled": True,  # Anonymous usage statistics
    "telemetry_uuid": "",
    "auto_update_check": True,  # Check for updates on startup
}


def load_config() -> dict:
    """Load configuration from config.json, initialize with defaults if not exists."""
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] Failed to read {CONFIG_FILE}: {e}")

    # Check and reset daily play time if date changed
    today = datetime.now().strftime("%Y-%m-%d")
    if config.get("daily_played_date") != today:
        config["daily_played_date"] = today
        config["daily_played_seconds"] = 0
        save_config(config)

    return config


def save_config(config: dict) -> bool:
    """Save configuration to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Config] Failed to save {CONFIG_FILE}: {e}")
        return False


def set_auto_start(enabled: bool) -> bool:
    """Register or remove program from Windows Startup Registry."""
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
        print(f"[Config] Auto-start configuration failed: {e}")
        return False
