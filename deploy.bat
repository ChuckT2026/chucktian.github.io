@echo off
cd /d "C:\Users\admin\WorkBuddy\2026-08-22-12-02-03\opc-site"
set PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files (x86)\Git\cmd
git add -A
git commit -m "site update" >nul 2>&1
git push
if %errorlevel% neq 0 (
  echo.
  echo ==========================================
  echo [ERROR] Push failed. Your site was NOT updated.
  echo.
  echo Common fixes:
  echo 1. Switch to mobile hotspot and run deploy.bat again.
  echo 2. Run: git config --global http.postBuffer 524288000
  echo 3. If using VPN/proxy, check Git is routing through it.
  echo ==========================================
  pause
  exit /b 1
)
echo.
echo Deploy done. Wait 1-3 min and refresh chucktian.com
pause
