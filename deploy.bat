@echo off
cd /d "C:\Users\admin\WorkBuddy\2026-08-22-12-02-03\opc-site"
set PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files (x86)\Git\cmd

git add -A
git commit -m "site update" >nul 2>&1

REM 提高传输稳定性，减少断线误判
git config --global http.postBuffer 524288000
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999

set MAX=3
set N=0

:retry
set /a N=N+1
echo [Attempt %N%/%MAX%] Pushing to GitHub...
git push
if %errorlevel% equ 0 goto success

if %N% lss %MAX% (
  echo.
  echo Push failed (network hiccup). Retrying in 3s...
  ping -n 4 127.0.0.1 >nul
  goto retry
)

echo.
echo ==========================================
echo [ERROR] Push failed after %MAX% attempts.
echo Your site was NOT updated.
echo.
echo Common fixes:
echo 1. Switch to mobile hotspot and run deploy.bat again.
echo 2. If using VPN/proxy, check Git routes through it.
echo ==========================================
pause
exit /b 1

:success
echo.
echo Deploy done. Wait 1-3 min and refresh chucktian.com
pause
