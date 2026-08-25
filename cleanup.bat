@echo off
chcp 65001 > nul
echo ========================================================
echo   DBjara (디비자라) 프로세스 및 자동실행 레지스트리 완벽 제거 툴
echo ========================================================
echo.

echo [1/3] 백그라운드에서 실행 중인 DBjara 관련 프로세스를 종료합니다...
taskkill /F /FI "WINDOWTITLE eq DBjara*" > nul 2>&1
wmic process where "commandline like '%%app.py%%' or commandline like '%%watchdog.py%%'" call terminate > nul 2>&1

echo [2/3] 윈도우 부팅 자동 실행 레지스트리를 삭제합니다...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DBjara" /f > nul 2>&1

echo [3/3] 임시 플래그 파일 및 잔여 설정을 정리합니다...
if exist "%~dp0dbjara_exit.flag" del /f /q "%~dp0dbjara_exit.flag"

echo.
echo ========================================================
echo   [성공] DBjara 자동 실행 및 프로세스가 완전히 제거되었습니다!
echo   이제 폴더 삭제 및 재부팅을 하셔도 깔끔하게 정리됩니다.
echo ========================================================
echo.
pause
