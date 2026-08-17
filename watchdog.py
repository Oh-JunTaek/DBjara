"""
Watchdog process for dbjara
Monitors the main dbjara app.py and relaunches it if it gets killed unexpectedly.
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
                # Main app died unexpectedly without killing watchdog -> Revive!
                print("[Watchdog] Main app process disappeared. Relaunching dbjara...")
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
