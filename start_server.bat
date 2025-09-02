@echo off
chcp 65001 >nul
echo 🚀 啟動 JobSpy 網頁服務器
echo.
echo 正在檢查 Python 環境...
if exist ".venv\Scripts\activate.bat" (
    echo ✅ 找到虛擬環境，正在啟動...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  未找到虛擬環境，使用系統 Python
)

echo.
echo 🌐 啟動網頁應用...
echo 📱 本地訪問: http://127.0.0.1:5000
echo 📱 網路訪問: http://192.168.1.181:5000
echo.
echo 按 Ctrl+C 停止服務器
echo.

cd web_app
python app.py

echo.
echo 👋 服務器已停止
pause