@echo off
chcp 65001 > nul
title Gang Roster Web Server
echo ========================================================
echo       ⚔️ GANG ROSTER WEB SERVER (เว็บทำเนียบรายชื่อแก๊ง)
echo ========================================================
echo.
echo [*] กำลังเริ่มเปิดเซิร์ฟเวอร์เว็บรายชื่อแก๊ง...
python server.py
pause
