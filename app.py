"""
DBjara 2.0 - 메인 애플리케이션 백그라운드 서비스
복합 통제 룰셋(솔로/파티/야간 독립 제어) 및 목표 약정 기간 시스템을 실시간으로 감시합니다.
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime, time as dtime
from typing import Optional

# 윈도우 알림 시 프로세스명이 'python' 대신 'DBjara'로 표시되도록 AppUserModelID 등록
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DBjara.App.1.0")
except Exception:
    pass

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


def create_tray_icon_image() -> Image.Image:
    """시스템 트레이용 달/방패 아이콘을 생성합니다."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 딥 슬레이트 네이비 배경
    draw.ellipse((4, 4, 60, 60), fill=(15, 23, 42, 255), outline=(56, 189, 248, 255), width=3)

    # 초승달 형상 (수면/통제 상징)
    draw.ellipse((16, 14, 48, 46), fill=(248, 250, 252, 255))
    draw.ellipse((22, 12, 54, 44), fill=(15, 23, 42, 255))

    # 인디고 별 포인트
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
        
        # 사전 10분 전 알림 플래그
        self.warned_solo_10min = False
        self.warned_party_10min = False
        
        # 현재 활성 세션이 솔로인지 파티인지 추적
        self.current_session_mode = "solo"  # "solo" or "party"

        # 익명 시작 통계 전송
        send_event_async(self.config, "app_start")

    def is_in_night_time(self) -> bool:
        """현재 시각이 야간 차단 시간대에 해당하는지 확인합니다."""
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
        """시스템 트레이 알림을 전송합니다. (단시간 연속 스팸 방지)"""
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
        """시작 시 최신 버전을 비동기로 확인합니다."""
        if not self.config.get("auto_update_check", True):
            return

        def _check():
            has_update, tag, _, url = get_latest_version_info()
            if has_update:
                self.notify(t("notif_update_title"), t("notif_update_msg", tag=tag))
        threading.Thread(target=_check, daemon=True).start()

    def monitor_loop(self):
        """핵심 백그라운드 고속 감시 루프 (0.15초 주기)"""
        print("[DBjara] 스마트 감시 루프가 활성화되었습니다.")
        last_save_time = time.time()
        last_second_tick = time.time()

        while self.running:
            try:
                now_sec = time.time()

                # 1. 야간 차단 체크 (최우선 순위 - 디비자라 모드)
                if self.config.get("night_lock", True) and self.is_in_night_time():
                    if self.lcu.is_league_running():
                        self.lcu.kill_league_client()
                        self.notify(t("notif_night_title"), t("notif_night_msg"))
                        send_event_async(self.config, "block_night")
                        time.sleep(1.0)
                        continue

                # 2. 롤 클라이언트 연결 및 매칭/플레이 상태 감시
                if self.lcu.is_league_running():
                    connected = self.lcu.is_connected() or self.lcu.connect()
                    if connected:
                        party_size = self.lcu.get_party_size()
                        search_state = self.lcu.get_matchmaking_search_state()
                        phase = self.lcu.get_gameflow_phase()

                        # 파티 상태 갱신
                        if party_size >= 2:
                            self.current_session_mode = "party"
                        elif party_size == 1:
                            self.current_session_mode = "solo"

                        solo_rule = self.config.get("solo_rule", "block_always")
                        party_rule = self.config.get("party_rule", "time_limit")
                        solo_limit_sec = self.config.get("solo_limit_minutes", 60) * 60
                        party_limit_sec = self.config.get("party_limit_minutes", 120) * 60

                        is_matching = (search_state in ("Searching", "Found") or phase in ("Matchmaking", "ReadyCheck"))

                        # [매칭 감지 및 차단]
                        if is_matching:
                            # 1인 솔로 큐 매칭 시도 시
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

                            # 2인 이상 다인큐 매칭 시도 시
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

                        # [인게임 시간 누적 및 10분 전 사전 알림]
                        if now_sec - last_second_tick >= 1.0:
                            delta = int(now_sec - last_second_tick)
                            last_second_tick = now_sec

                            if phase in ("ChampSelect", "InProgress", "GameStart", "Reconnect"):
                                # 솔로 플레이 진행 중
                                if self.current_session_mode == "solo":
                                    self.config["daily_solo_played_seconds"] = self.config.get("daily_solo_played_seconds", 0) + delta
                                    s_played = self.config["daily_solo_played_seconds"]
                                    if solo_rule == "time_limit":
                                        rem = max(0, solo_limit_sec - s_played)
                                        if rem <= 600 and not self.warned_solo_10min:
                                            self.warned_solo_10min = True
                                            self.notify(t("notif_time_warn_title"), t("notif_time_warn_msg"))

                                # 파티 플레이 진행 중
                                elif self.current_session_mode == "party":
                                    self.config["daily_party_played_seconds"] = self.config.get("daily_party_played_seconds", 0) + delta
                                    p_played = self.config["daily_party_played_seconds"]
                                    if party_rule == "time_limit":
                                        rem = max(0, party_limit_sec - p_played)
                                        if rem <= 600 and not self.warned_party_10min:
                                            self.warned_party_10min = True
                                            self.notify(t("notif_time_warn_title"), t("notif_time_warn_msg"))

                # 30초마다 설정 및 누적 시간 자동 저장
                if now_sec - last_save_time > 30:
                    save_config(self.config)
                    last_save_time = now_sec

            except Exception as e:
                print(f"[DBjara] 감시 루프 오류: {e}")

            time.sleep(0.15)

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
        """설정 변경 콜백"""
        self.config = new_config
        set_language(self.config.get("language", "ko"))
        self.riot_validator = RiotAPIValidator(api_key=self.config.get("riot_api_key", ""))
        self.warned_solo_10min = False
        self.warned_party_10min = False

    def open_settings_ui(self):
        """설정 창 열기"""
        win = SettingsWindow(on_config_updated=self.on_config_updated)
        win.mainloop()

    def request_exit(self):
        """프로그램 종료 요청 (약정 기간 잠금 중이거나 OTP 켜져있으면 마스터키/OTP 요구)"""
        is_locked = is_commitment_locked(self.config)
        has_otp = self.config.get("otp_enabled", False) and self.config.get("otp_secret")

        if is_locked or has_otp:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            OTPAuthDialog(
                root, self.config.get("otp_secret", ""),
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

        # 2. 업데이트 비동기 확인
        self.check_updates_async()

        # 3. 백그라운드 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()

        # 4. 시스템 트레이 메뉴 구성
        def get_status_text(item):
            plan_name = self.config.get("commitment_plan", "none")
            return f"{t('tray_plan_prefix')}{t('tray_plan_' + plan_name)}"

        menu = pystray.Menu(
            pystray.MenuItem(get_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_open_settings"), lambda: threading.Thread(target=self.open_settings_ui, daemon=True).start()),
            pystray.MenuItem(lambda item: t("tray_check_update"), lambda: threading.Thread(target=lambda: open_release_page(), daemon=True).start()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_exit"), lambda: threading.Thread(target=self.request_exit, daemon=True).start()),
        )

        icon_image = create_tray_icon_image()
        self.tray_icon = pystray.Icon("DBjara", icon_image, "DBjara - LoL Control Solution", menu)

        print("[DBjara] 시스템 트레이 서비스가 시작되었습니다.")
        self.tray_icon.run()


if __name__ == "__main__":
    app = DBjaraApp()
    app.run()
