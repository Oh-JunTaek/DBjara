"""
DBjara - 작업 관리자 강제 종료 방지 (Watchdog) 모듈
메인 프로그램(app.py)의 프로세스 ID를 감시하다가 예기치 않게 종료되면 즉시 재실행합니다.
"""

import sys
import time
import os
import subprocess
import psutil


def main():
    if len(sys.argv) < 2:
        return

    main_pid = int(sys.argv[1])
    python_exe = sys.executable
    app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

    while True:
        try:
            if not psutil.pid_exists(main_pid):
                # 메인 프로그램이 비정상 종료된 경우 (정상 종료 시 watchdog도 함께 종료됨)
                print("[Watchdog] 메인 프로그램이 종료됨을 감지했습니다. DBjara를 재실행합니다...")
                subprocess.Popen(
                    [python_exe, app_script],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                break
        except Exception:
            pass

        time.sleep(1.5)


if __name__ == "__main__":
    main()
