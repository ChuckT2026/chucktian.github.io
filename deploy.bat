@echo off
chcp 65001 >nul
cd /d "C:\Users\admin\WorkBuddy\2026-08-22-12-02-03\opc-site"
git add -A
git commit -m "site update" >nul 2>&1
git push
echo.
echo ============================================
echo  部署已提交。等待 1-3 分钟后刷新即可看到更新。
echo  网址: http://chucktian.com
echo ============================================
echo.
pause
