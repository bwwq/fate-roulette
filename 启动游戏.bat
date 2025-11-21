@echo off
chcp 65001 >nul
echo ================================
echo   命运轮盘 - Fate Roulette
echo ================================
echo.
echo 正在启动游戏服务器...
echo.
echo 服务器地址: http://localhost:3000
echo.
echo 请在浏览器中打开上述地址开始游戏
echo.
echo 按 Ctrl+C 停止服务器
echo ================================
echo.

cd /d "%~dp0"
node server.js

pause
