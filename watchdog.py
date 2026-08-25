"""
DBjara - 작업 관리자 강제 종료 방지 (Watchdog) 모듈
메인 프로그램(app.py)의 프로세스 ID를 감시하다가 예기치 않게 종료되면 즉시 재실행합니다.
"""

import sys
import time
import os
import subprocess
import psutil

EXIT_FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dbjara_exit.flag")


def main():
    if len(sys.argv) < 2:
        return

    main_pid = int(sys.argv[1])
    python_exe = sys.executable
    app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

    while True:
        try:
            # 사용자가 정상 종료를 요청하여 exit 플래그 파일이 생성된 경우 watchdog도 조용히 종료
            if os.path.exists(EXIT_FLAG_FILE):
                try:
                    os.remove(EXIT_FLAG_FILE)
                except Exception:
                    pass
                break

            # 메인 프로세스가 강제 종료되었는지 검사
            if not psutil.pid_exists(main_pid):
                # 잠시 후 플래그 재확인 (정상 종료 과정 중 딜레이 대비)
                time.sleep(0.5)
                if os.path.exists(EXIT_FLAG_FILE):
                    try:
                        os.remove(EXIT_FLAG_FILE)
                    except Exception:
                        pass
                    break

                print("[Watchdog] 메인 프로그램이 비정상 종료됨을 감지했습니다. DBjara를 재실행합니다...")
                subprocess.Popen(
                    [python_exe, app_script],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                break
        except Exception:
            pass

        time.sleep(1.0)


if __name__ == "__main__":
    main()
