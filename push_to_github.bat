@echo off
chcp 65001 > nul
title Push Gang Roster Web to GitHub
echo ========================================================
echo       🚀 PUSH GANG ROSTER WEB TO GITHUB
echo ========================================================
echo.
echo [*] กำลังส่งโค้ดขึ้น GitHub Repository: gang-roster-web...
git push -u origin main
echo.
echo ========================================================
echo เสร็จสิ้น
echo ========================================================
pause
