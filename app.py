"""
DBjara 2.0 - 메인 애플리케이션 백그라운드 서비스
Tkinter 메인 스레드 이벤트 큐 관리로 트레이 우클릭 메뉴 및 설정창이 100% 즉시 동작하도록 보장합니다.
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime, time as dtime
from typing import Optional

# 윈도우 프로세스 이름 및 AppUserModelID 설정
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW("DBjara")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DBjara.App.1.0")
except Exception:
    pass

# 단일 인스턴스 (Single Instance Mutex) 중복 실행 차단
_mutex_handle = None
def ensure_single_instance():
    global _mutex_handle
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            mutex_name = "Global\\DBjara_SingleInstance_Mutex"
            _mutex_handle = kernel32.CreateMutexW(None, True, mutex_name)
            last_error = kernel32.GetLastError()
            ERROR_ALREADY_EXISTS = 183
            if last_error == ERROR_ALREADY_EXISTS:
                print("[DBjara] 이미 DBjara 프로세스가 실행 중입니다. 중복 실행을 차단하고 종료합니다.")
                sys.exit(0)
        except Exception:
            pass

ensure_single_instance()

import tkinter as tk
from PIL import Image, ImageDraw
import pystray

from config import load_config, save_config, is_commitment_locked
from totp import verify_totp
from lcu import LCUClient
from gui import SettingsWindow, OTPAuthDialog
from updater import get_latest_version_info, open_release_page, CURRENT_VERSION
from telemetry import send_event_async
from riot_api import RiotAPIValidator
from i18n import t, set_language

EXIT_FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dbjara_exit.flag")


def create_tray_icon_image() -> Image.Image:
    """시스템 트레이용 아이콘 이미지를 동적으로 생성합니다."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse((4, 4, 60, 60), fill=(15, 23, 42, 255), outline=(56, 189, 248, 255), width=3)
    draw.ellipse((16, 14, 48, 46), fill=(248, 250, 252, 255))
    draw.ellipse((22, 12, 54, 44), fill=(15, 23, 42, 255))

    draw.point((42, 20), fill=(129, 140, 248, 255))
    draw.point((44, 22), fill=(129, 140, 248, 255))
    draw.point((40, 22), fill=(129, 140, 248, 255))
    draw.point((42, 24), fill=(129, 140, 248, 255))

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
        
        self.warned_solo_10min = False
        self.warned_party_10min = False
        self.current_session_mode = "solo"

        # 메인 스레드 GUI 이벤트 플래그 (스레드 안전성 보장)
        self.req_open_settings = False
        self.req_exit = False
        self.settings_window_active = False

        # 메인 Tk 숨김 루트 객체 (메인 스레드 유지용)
        self.tk_root: Optional[tk.Tk] = None

        # 앱 실행 익명 통계 전송
        send_event_async(self.config, "app_start")

    def is_in_night_time(self) -> bool:
        """야간 차단 시간대 확인"""
        try:
            start_str = self.config.get("night_start", "23:00")
            if start_str == "24:00":
                start_str = "00:00"
            end_str = self.config.get("night_end", "07:00")

            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))

            now = datetime.now().time()
            t_start = dtime(start_h, start_m)
            t_end = dtime(end_h, end_m)

            if t_start > t_end:
                return now >= t_start or now <= t_end
            else:
                return t_start <= now <= t_end
        except Exception:
            return False

    def notify(self, title: str, message: str):
        now = time.time()
        if now - self.last_notification_time < 4:
            return
        self.last_notification_time = now

        if self.tray_icon and self.tray_icon.visible:
            try:
                self.tray_icon.notify(message, title)
            except Exception:
                pass

    def check_updates_async(self):
        if not self.config.get("auto_update_check", True):
            return

        def _check():
            has_update, tag, _, url = get_latest_version_info()
            if has_update:
                self.notify(t("notif_update_title"), t("notif_update_msg", tag=tag))
        threading.Thread(target=_check, daemon=True).start()

    def monitor_loop(self):
        """핵심 백그라운드 모니터링 루프 (0.15초 고속 주기)"""
        print("[DBjara] 백그라운드 감시 루프가 활성화되었습니다.")
        last_save_time = time.time()
        last_second_tick = time.time()

        while self.running:
            try:
                now_sec = time.time()

                # 1. 야간 차단 체크
                if self.config.get("night_lock", True) and self.is_in_night_time():
                    if self.lcu.is_league_running():
                        self.lcu.kill_league_client()
                        self.notify(t("notif_night_title"), t("notif_night_msg"))
                        send_event_async(self.config, "block_night")
                        time.sleep(1.0)
                        continue

                # 2. LCU 감시 및 조건부 차단
                if self.lcu.is_league_running():
                    connected = self.lcu.is_connected() or self.lcu.connect()
                    if connected:
                        party_size = self.lcu.get_party_size()
                        search_state = self.lcu.get_matchmaking_search_state()
                        phase = self.lcu.get_gameflow_phase()

                        if party_size >= 2:
                            self.current_session_mode = "party"
                        elif party_size == 1:
                            self.current_session_mode = "solo"

                        solo_rule = self.config.get("solo_rule", "block_always")
                        party_rule = self.config.get("party_rule", "time_limit")
                        solo_limit_sec = self.config.get("solo_limit_minutes", 60) * 60
                        party_limit_sec = self.config.get("party_limit_minutes", 120) * 60

                        is_matching = (search_state in ("Searching", "Found") or phase in ("Matchmaking", "ReadyCheck"))

                        # [매칭 조건별 차단]
                        if is_matching:
                            if self.current_session_mode == "solo" and party_size <= 1:
                                if solo_rule == "block_always":
                                    if self.lcu.cancel_matchmaking():
                                        self.notify(t("notif_solo_block_title"), t("notif_solo_block_msg"))
                                        send_event_async(self.config, "block_solo_always")

                                elif solo_rule == "time_limit":
                                    if self.config.get("daily_solo_played_seconds", 0) >= solo_limit_sec:
                                        if self.lcu.cancel_matchmaking():
                                            self.notify(t("notif_solo_time_over_title"), t("notif_solo_time_over_msg"))
                                            send_event_async(self.config, "block_solo_time_over")

                            elif self.current_session_mode == "party" or party_size >= 2:
                                if party_rule == "block_always":
                                    if self.lcu.cancel_matchmaking():
                                        self.notify(t("notif_party_block_title"), t("notif_party_block_msg"))
                                        send_event_async(self.config, "block_party_always")

                                elif party_rule == "time_limit":
                                    if self.config.get("daily_party_played_seconds", 0) >= party_limit_sec:
                                        if self.lcu.cancel_matchmaking():
                                            self.notify(t("notif_party_time_over_title"), t("notif_party_time_over_msg"))
                                            send_event_async(self.config, "block_party_time_over")

                        # [인게임 시간 누적]
                        if now_sec - last_second_tick >= 1.0:
                            delta = int(now_sec - last_second_tick)
                            last_second_tick = now_sec

                            if phase in ("ChampSelect", "InProgress", "GameStart", "Reconnect"):
                                if self.current_session_mode == "solo":
                                    self.config["daily_solo_played_seconds"] = self.config.get("daily_solo_played_seconds", 0) + delta
                                    s_played = self.config["daily_solo_played_seconds"]
                                    if solo_rule == "time_limit":
                                        rem = max(0, solo_limit_sec - s_played)
                                        if rem <= 600 and not self.warned_solo_10min:
                                            self.warned_solo_10min = True
                                            self.notify(t("notif_time_warn_title"), t("notif_time_warn_msg"))

                                elif self.current_session_mode == "party":
                                    self.config["daily_party_played_seconds"] = self.config.get("daily_party_played_seconds", 0) + delta
                                    p_played = self.config["daily_party_played_seconds"]
                                    if party_rule == "time_limit":
                                        rem = max(0, party_limit_sec - p_played)
                                        if rem <= 600 and not self.warned_party_10min:
                                            self.warned_party_10min = True
                                            self.notify(t("notif_time_warn_title"), t("notif_time_warn_msg"))

                if now_sec - last_save_time > 30:
                    save_config(self.config)
                    last_save_time = now_sec

            except Exception as e:
                print(f"[DBjara] 감시 루프 오류: {e}")

            time.sleep(0.15)

    def launch_watchdog(self):
        """Watchdog 프로세스 실행"""
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
        self.config = new_config
        set_language(self.config.get("language", "ko"))
        self.riot_validator = RiotAPIValidator(api_key=self.config.get("riot_api_key", ""))
        self.warned_solo_10min = False
        self.warned_party_10min = False

    def handle_open_settings_main_thread(self):
        """메인 스레드에서 안전하게 설정 창을 엽니다."""
        if self.settings_window_active:
            return
        self.settings_window_active = True

        # 약정 잠금이나 OTP가 켜져 있는지 확인
        is_locked = is_commitment_locked(self.config)
        has_otp = self.config.get("otp_enabled", False) and self.config.get("otp_secret")

        def _open():
            win = SettingsWindow(on_config_updated=self.on_config_updated)
            win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), setattr(self, 'settings_window_active', False)))
            win.mainloop()
            self.settings_window_active = False

        if is_locked or has_otp:
            OTPAuthDialog(
                self.tk_root, self.config.get("otp_secret", ""),
                on_success=_open
            )
        else:
            _open()

    def handle_exit_main_thread(self):
        """메인 스레드에서 종료 요구 처리"""
        is_locked = is_commitment_locked(self.config)
        has_otp = self.config.get("otp_enabled", False) and self.config.get("otp_secret")

        if is_locked or has_otp:
            OTPAuthDialog(
                self.tk_root, self.config.get("otp_secret", ""),
                on_success=self.execute_final_exit
            )
        else:
            self.execute_final_exit()

    def execute_final_exit(self):
        """프로세스 및 watchdog 즉시 완전 종료"""
        self.running = False
        save_config(self.config)

        try:
            with open(EXIT_FLAG_FILE, "w", encoding="utf-8") as f:
                f.write("EXIT")
        except Exception:
            pass

        if self.watchdog_process:
            try:
                self.watchdog_process.kill()
            except Exception:
                pass

        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass

        if self.tk_root:
            try:
                self.tk_root.destroy()
            except Exception:
                pass

        os._exit(0)

    def main_thread_event_loop(self):
        """메인 스레드에서 100ms마다 트레이 메뉴 클릭 요청(설정 열기, 종료)을 검사하는 이벤트 루프"""
        if self.req_open_settings:
            self.req_open_settings = False
            self.handle_open_settings_main_thread()

        if self.req_exit:
            self.req_exit = False
            self.handle_exit_main_thread()

        if self.running and self.tk_root:
            self.tk_root.after(100, self.main_thread_event_loop)

    def run(self):
        # 1. 이전 exit 플래그 정리
        if os.path.exists(EXIT_FLAG_FILE):
            try:
                os.remove(EXIT_FLAG_FILE)
            except Exception:
                pass

        # 2. Watchdog 백그라운드 실행
        self.launch_watchdog()

        # 3. 비동기 업데이트 확인
        self.check_updates_async()

        # 4. 감시 루프 스레드 실행
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()

        # 5. 시스템 트레이 메뉴 구성 (스레드 안전 플래그만 세움)
        def get_status_text(item):
            plan_name = self.config.get("commitment_plan", "none")
            return f"{t('tray_plan_prefix')}{t('tray_plan_' + plan_name)}"

        menu = pystray.Menu(
            pystray.MenuItem(get_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_open_settings"), lambda: setattr(self, 'req_open_settings', True)),
            pystray.MenuItem(lambda item: t("tray_check_update"), lambda: threading.Thread(target=lambda: open_release_page(), daemon=True).start()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_exit"), lambda: setattr(self, 'req_exit', True)),
        )

        icon_image = create_tray_icon_image()
        self.tray_icon = pystray.Icon("DBjara", icon_image, "DBjara - LoL Control Solution", menu)

        # 트레이 아이콘을 비동기 스레드에서 실행
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

        print("[DBjara] 메인 애플리케이션 및 시스템 트레이 서비스가 실행되었습니다.")

        # 메인 스레드: Tkinter 메인 루트 이벤트 루프 가동 (스레드 안전성 100% 보장)
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
        self.tk_root.after(100, self.main_thread_event_loop)
        self.tk_root.mainloop()


if __name__ == "__main__":
    app = DBjaraApp()
    app.run()
