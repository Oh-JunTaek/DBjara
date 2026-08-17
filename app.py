"""
DBjara (디비자라) Main Application
System Tray Background Monitor for League of Legends Solo Rank Blocker.
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime, time as dtime
from typing import Optional

from PIL import Image, ImageDraw
import pystray

from config import load_config, save_config
from totp import verify_totp
from lcu import LCUClient
from gui import SettingsWindow, OTPAuthDialog
from updater import get_latest_version_info, open_release_page, CURRENT_VERSION
from telemetry import send_event_async
from riot_api import RiotAPIValidator


def create_tray_icon_image() -> Image.Image:
    """Generate a clean moon/shield icon for system tray."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circle background (Dark Blue)
    draw.ellipse((4, 4, 60, 60), fill=(26, 30, 36, 255), outline=(59, 130, 246, 255), width=3)

    # Crescent Moon shape for "DBjara" (Sleep/Night)
    draw.ellipse((16, 14, 48, 46), fill=(243, 244, 246, 255))
    draw.ellipse((22, 12, 54, 44), fill=(26, 30, 36, 255))

    # Star accent
    draw.point((42, 20), fill=(59, 130, 246, 255))
    draw.point((44, 22), fill=(59, 130, 246, 255))
    draw.point((40, 22), fill=(59, 130, 246, 255))
    draw.point((42, 24), fill=(59, 130, 246, 255))

    return img


class DBjaraApp:
    def __init__(self):
        self.config = load_config()
        self.lcu = LCUClient()
        self.running = True
        self.tray_icon: Optional[pystray.Icon] = None
        self.last_notification_time = 0
        self.watchdog_process: Optional[subprocess.Popen] = None
        self.riot_validator = RiotAPIValidator(api_key=self.config.get("riot_api_key", ""))

        # Send anonymous startup event
        send_event_async(self.config, "app_start")

    def is_in_night_time(self) -> bool:
        """Check if current system time falls into night lock range."""
        try:
            start_h, start_m = map(int, self.config.get("night_start", "23:00").split(":"))
            end_h, end_m = map(int, self.config.get("night_end", "07:00").split(":"))

            now = datetime.now().time()
            t_start = dtime(start_h, start_m)
            t_end = dtime(end_h, end_m)

            if t_start > t_end:  # Crosses midnight (e.g. 23:00 -> 07:00)
                return now >= t_start or now <= t_end
            else:
                return t_start <= now <= t_end
        except Exception:
            return False

    def notify(self, title: str, message: str):
        """Send notification via system tray with throttle."""
        now = time.time()
        if now - self.last_notification_time < 5:
            return
        self.last_notification_time = now

        if self.tray_icon and self.tray_icon.visible:
            try:
                self.tray_icon.notify(message, title)
            except Exception:
                pass

    def check_updates_async(self):
        """Check for updates on startup if enabled."""
        if not self.config.get("auto_update_check", True):
            return

        def _check():
            has_update, tag, _, url = get_latest_version_info()
            if has_update:
                self.notify("🎉 DBjara 새 버전 업데이트 알림", f"새로운 버전 ({tag})이 출시되었습니다!\n트레이 메뉴의 설정을 열어 확인하세요.")
        threading.Thread(target=_check, daemon=True).start()

    def monitor_loop(self):
        """Core background monitoring loop."""
        print("[DBjara] Background monitoring loop started.")
        last_save_time = time.time()

        while self.running:
            try:
                # 1. Check Night Lock (Highest Priority - '디비자라' 모드)
                if self.config.get("night_lock", True) and self.is_in_night_time():
                    if self.lcu.is_league_running():
                        self.lcu.kill_league_client()
                        self.notify("🌙 DBjara - 야간 강제 차단", "야간 시간대입니다! 게임이 즉시 종료되었습니다. 어서 주무세요.")
                        send_event_async(self.config, "block_night")
                        time.sleep(2)
                        continue

                # 2. Check High Mode (Block Game Entirely)
                mode = self.config.get("mode", "medium")
                if mode == "high":
                    if self.lcu.is_league_running():
                        self.lcu.kill_league_client()
                        self.notify("🛑 DBjara - 실행 차단", "통제 강도 [상] 설정으로 인해 롤 실행이 차단되었습니다.")
                        send_event_async(self.config, "block_high")
                        time.sleep(2)
                        continue

                # 3. Check Medium & Low Modes (LCU API Control)
                if self.lcu.is_league_running():
                    connected = self.lcu.is_connected() or self.lcu.connect()
                    if connected:
                        party_size = self.lcu.get_party_size()
                        search_state = self.lcu.get_matchmaking_search_state()
                        phase = self.lcu.get_gameflow_phase()

                        # Medium Mode: Solo Queue Cancel
                        if mode == "medium":
                            if party_size == 1:
                                if search_state == "Searching" or phase in ("Matchmaking", "ReadyCheck"):
                                    if self.lcu.cancel_matchmaking():
                                        self.notify("🚫 DBjara - 솔로 매칭 취소", "1인 솔로 랭크 매칭이 감지되어 취소되었습니다!\n(2인 이상 다인큐만 가능합니다)")
                                        send_event_async(self.config, "block_solo_cancel")

                        # Low Mode: Daily Play Time Tracking
                        elif mode == "low":
                            if party_size == 1 and phase == "InProgress":
                                # Accumulate solo play seconds
                                self.config["daily_played_seconds"] = self.config.get("daily_played_seconds", 0) + 1
                                limit_sec = self.config.get("daily_limit_minutes", 120) * 60

                                if self.config["daily_played_seconds"] >= limit_sec:
                                    self.lcu.kill_league_client()
                                    self.notify("⏰ DBjara - 일일 시간 초과", f"오늘의 솔로 허용 시간({self.config.get('daily_limit_minutes')}분)을 모두 소진하여 종료되었습니다.")
                                    send_event_async(self.config, "block_time_limit")

                            elif party_size == 1 and (search_state == "Searching" or phase in ("Matchmaking", "ReadyCheck")):
                                limit_sec = self.config.get("daily_limit_minutes", 120) * 60
                                if self.config.get("daily_played_seconds", 0) >= limit_sec:
                                    self.lcu.cancel_matchmaking()
                                    self.notify("⏰ DBjara - 솔로 매칭 차단", "오늘의 일일 솔로 허용 시간을 모두 초과하여 매칭이 차단되었습니다.")

                # Save play time every 30 seconds
                if time.time() - last_save_time > 30:
                    save_config(self.config)
                    last_save_time = time.time()

            except Exception as e:
                print(f"[DBjara] Monitor Loop error: {e}")

            time.sleep(1.0)

    def launch_watchdog(self):
        """Launch background watchdog process to prevent force termination."""
        try:
            watchdog_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchdog.py")
            if os.path.exists(watchdog_script):
                python_exe = sys.executable
                self.watchdog_process = subprocess.Popen(
                    [python_exe, watchdog_script, str(os.getpid())],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
        except Exception as e:
            print(f"[DBjara] Failed to launch watchdog: {e}")

    def on_config_updated(self, new_config: dict):
        """Callback when user saves new settings from GUI."""
        self.config = new_config
        self.riot_validator = RiotAPIValidator(api_key=self.config.get("riot_api_key", ""))

    def open_settings_ui(self):
        """Open Settings Window with OTP authorization if required."""
        if self.config.get("otp_enabled", False) and self.config.get("otp_secret"):
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            OTPAuthDialog(
                root, self.config.get("otp_secret"),
                on_success=lambda: self._show_settings_window(root)
            )
            root.mainloop()
        else:
            self._show_settings_window(None)

    def _show_settings_window(self, temp_root):
        if temp_root:
            temp_root.destroy()
        win = SettingsWindow(on_config_updated=self.on_config_updated)
        win.mainloop()

    def request_exit(self):
        """Exit application, requiring OTP verification if enabled."""
        if self.config.get("otp_enabled", False) and self.config.get("otp_secret"):
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            OTPAuthDialog(
                root, self.config.get("otp_secret"),
                on_success=lambda: self._do_exit(root)
            )
            root.mainloop()
        else:
            self._do_exit(None)

    def _do_exit(self, temp_root):
        if temp_root:
            temp_root.destroy()
        self.running = False
        save_config(self.config)
        if self.watchdog_process:
            try:
                self.watchdog_process.kill()
            except Exception:
                pass
        if self.tray_icon:
            self.tray_icon.stop()
        sys.exit(0)

    def run(self):
        # 1. Start watchdog
        self.launch_watchdog()

        # 2. Check updates on launch
        self.check_updates_async()

        # 3. Start monitoring background thread
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()

        # 4. Setup System Tray Menu
        def get_status_text(item):
            mode_names = {"high": "상 (전체 차단)", "medium": "중 (솔로 금지)", "low": "하 (시간 제한)"}
            m_str = mode_names.get(self.config.get("mode", "medium"), "중")
            return f"통제 모드: {m_str}"

        menu = pystray.Menu(
            pystray.MenuItem(get_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ 설정 열기 (DBjara)", lambda: threading.Thread(target=self.open_settings_ui, daemon=True).start()),
            pystray.MenuItem("🔄 업데이트 확인", lambda: threading.Thread(target=lambda: open_release_page(), daemon=True).start()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ DBjara 종료", lambda: threading.Thread(target=self.request_exit, daemon=True).start()),
        )

        icon_image = create_tray_icon_image()
        self.tray_icon = pystray.Icon("DBjara", icon_image, "디비자라 (DBjara) - LoL 통제기", menu)

        print("[DBjara] Tray icon is running. Check system tray.")
        self.tray_icon.run()


if __name__ == "__main__":
    app = DBjaraApp()
    app.run()
