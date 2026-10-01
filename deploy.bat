@echo off
cd /d "C:\Users\admin\WorkBuddy\2026-08-22-12-02-03\opc-site"
set PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files (x86)\Git\cmd
git add -A
git commit -m "site update" >nul 2>&1
git push
echo.
echo Deploy done. Wait 1-3 min and refresh chucktian.com
pause
