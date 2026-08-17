"""
DBjara (디비자라) 메인 애플리케이션
롤 솔로 랭크 차단 및 야간 강제 종료를 수행하는 시스템 트레이 백그라운드 서비스입니다.
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
from i18n import t, set_language


def create_tray_icon_image() -> Image.Image:
    """시스템 트레이용 아이콘 이미지를 동적으로 생성합니다."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 원형 배경 (다크 블루)
    draw.ellipse((4, 4, 60, 60), fill=(26, 30, 36, 255), outline=(59, 130, 246, 255), width=3)

    # 달 모양 (수면/야간 상징)
    draw.ellipse((16, 14, 48, 46), fill=(243, 244, 246, 255))
    draw.ellipse((22, 12, 54, 44), fill=(26, 30, 36, 255))

    # 별 포인트
    draw.point((42, 20), fill=(59, 130, 246, 255))
    draw.point((44, 22), fill=(59, 130, 246, 255))
    draw.point((40, 22), fill=(59, 130, 246, 255))
    draw.point((42, 24), fill=(59, 130, 246, 255))

    return img


class DBjaraApp:
    def __init__(self):
        self.config = load_config()
        set_language(self.config.get("language", "ko"))
        self.lcu = LCUClient()
        self.running = True
        self.tray_icon: Optional[pystray.Icon] = None
        self.last_notification_time = 0
        self.watchdog_process: Optional[subprocess.Popen] = None
        self.riot_validator = RiotAPIValidator(api_key=self.config.get("riot_api_key", ""))

        # 앱 실행 익명 이벤트 전송
        send_event_async(self.config, "app_start")

    def is_in_night_time(self) -> bool:
        """현재 시각이 야간 차단 시간대에 해당하는지 확인합니다."""
        try:
            start_h, start_m = map(int, self.config.get("night_start", "23:00").split(":"))
            end_h, end_m = map(int, self.config.get("night_end", "07:00").split(":"))

            now = datetime.now().time()
            t_start = dtime(start_h, start_m)
            t_end = dtime(end_h, end_m)

            if t_start > t_end:  # 자정을 넘는 경우 (예: 23:00 ~ 07:00)
                return now >= t_start or now <= t_end
            else:
                return t_start <= now <= t_end
        except Exception:
            return False

    def notify(self, title: str, message: str):
        """시스템 트레이 알림을 전송합니다. (단시간 연속 알림 방지)"""
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
        """프로그램 시작 시 최신 버전 업데이트 여부를 비동기로 확인합니다."""
        if not self.config.get("auto_update_check", True):
            return

        def _check():
            has_update, tag, _, url = get_latest_version_info()
            if has_update:
                self.notify(t("notif_update_title"), t("notif_update_msg", tag=tag))
        threading.Thread(target=_check, daemon=True).start()

    def monitor_loop(self):
        """핵심 백그라운드 감시 루프입니다."""
        print("[DBjara] 백그라운드 감시 루프가 시작되었습니다.")
        last_save_time = time.time()

        while self.running:
            try:
                # 1. 야간 차단 체크 (최우선 순위 - 디비자라 모드)
                if self.config.get("night_lock", True) and self.is_in_night_time():
                    if self.lcu.is_league_running():
                        self.lcu.kill_league_client()
                        self.notify(t("notif_night_title"), t("notif_night_msg"))
                        send_event_async(self.config, "block_night")
                        time.sleep(2)
                        continue

                # 2. '상' 모드 체크 (게임 실행 자체 차단)
                mode = self.config.get("mode", "medium")
                if mode == "high":
                    if self.lcu.is_league_running():
                        self.lcu.kill_league_client()
                        self.notify(t("notif_high_title"), t("notif_high_msg"))
                        send_event_async(self.config, "block_high")
                        time.sleep(2)
                        continue

                # 3. '중' 및 '하' 모드 체크 (LCU API 제어)
                if self.lcu.is_league_running():
                    connected = self.lcu.is_connected() or self.lcu.connect()
                    if connected:
                        party_size = self.lcu.get_party_size()
                        search_state = self.lcu.get_matchmaking_search_state()
                        phase = self.lcu.get_gameflow_phase()

                        # '중' 모드: 1인 솔로 큐 매칭 즉시 취소
                        if mode == "medium":
                            if party_size == 1:
                                if search_state == "Searching" or phase in ("Matchmaking", "ReadyCheck"):
                                    if self.lcu.cancel_matchmaking():
                                        self.notify(t("notif_solo_title"), t("notif_solo_msg"))
                                        send_event_async(self.config, "block_solo_cancel")

                        # '하' 모드: 일일 솔로 시간 누적 및 제한
                        elif mode == "low":
                            if party_size == 1 and phase == "InProgress":
                                # 솔로 플레이 진행 시간(초) 누적
                                self.config["daily_played_seconds"] = self.config.get("daily_played_seconds", 0) + 1
                                limit_sec = self.config.get("daily_limit_minutes", 120) * 60

                                if self.config["daily_played_seconds"] >= limit_sec:
                                    self.lcu.kill_league_client()
                                    self.notify(t("notif_time_title"), t("notif_time_msg", minutes=self.config.get("daily_limit_minutes")))
                                    send_event_async(self.config, "block_time_limit")

                            elif party_size == 1 and (search_state == "Searching" or phase in ("Matchmaking", "ReadyCheck")):
                                limit_sec = self.config.get("daily_limit_minutes", 120) * 60
                                if self.config.get("daily_played_seconds", 0) >= limit_sec:
                                    self.lcu.cancel_matchmaking()
                                    self.notify(t("notif_solo_title"), t("notif_time_block_msg"))

                # 30초마다 설정 및 누적 플레이 시간 저장
                if time.time() - last_save_time > 30:
                    save_config(self.config)
                    last_save_time = time.time()

            except Exception as e:
                print(f"[DBjara] 감시 루프 오류: {e}")

            time.sleep(1.0)

    def launch_watchdog(self):
        """강제 종료 방지를 위한 Watchdog 프로세스를 백그라운드로 실행합니다."""
        try:
            watchdog_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchdog.py")
            if os.path.exists(watchdog_script):
                python_exe = sys.executable
                self.watchdog_process = subprocess.Popen(
                    [python_exe, watchdog_script, str(os.getpid())],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
        except Exception as e:
            print(f"[DBjara] Watchdog 실행 실패: {e}")

    def on_config_updated(self, new_config: dict):
        """GUI에서 사용자가 설정을 변경하고 저장했을 때의 콜백입니다."""
        self.config = new_config
        set_language(self.config.get("language", "ko"))
        self.riot_validator = RiotAPIValidator(api_key=self.config.get("riot_api_key", ""))

    def open_settings_ui(self):
        """설정 창을 엽니다. (OTP가 활성화되어 있으면 먼저 인증을 요구)"""
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
        """프로그램 종료를 요청합니다. (OTP가 활성화되어 있으면 인증 필요)"""
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
        # 1. Watchdog 시작
        self.launch_watchdog()

        # 2. 시작 시 업데이트 확인
        self.check_updates_async()

        # 3. 백그라운드 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()

        # 4. 시스템 트레이 메뉴 구성
        def get_status_text(item):
            mode_names = {"high": t("tray_mode_high"), "medium": t("tray_mode_medium"), "low": t("tray_mode_low")}
            m_str = mode_names.get(self.config.get("mode", "medium"), "중")
            return f"{t('tray_status_prefix')}{m_str}"

        menu = pystray.Menu(
            pystray.MenuItem(get_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_open_settings"), lambda: threading.Thread(target=self.open_settings_ui, daemon=True).start()),
            pystray.MenuItem(lambda item: t("tray_check_update"), lambda: threading.Thread(target=lambda: open_release_page(), daemon=True).start()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_exit"), lambda: threading.Thread(target=self.request_exit, daemon=True).start()),
        )

        icon_image = create_tray_icon_image()
        self.tray_icon = pystray.Icon("DBjara", icon_image, "DBjara - LoL Solo Blocker", menu)

        print("[DBjara] 시스템 트레이 아이콘이 실행되었습니다.")
        self.tray_icon.run()


if __name__ == "__main__":
    app = DBjaraApp()
    app.run()
