@echo off
echo 🚀 启动 JobSpy 生产服务器
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo ✅ 启动虚拟环境...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo ✅ 启动虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ 未找到虚拟环境，使用系统 Python
)

echo.
echo 🌐 启动生产服务器...
echo 📱 本地访问: http://localhost:5000
echo 📱 网络访问: http://192.168.1.181:5000
echo 📊 API 文档: http://localhost:5000/api/sites
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动生产服务器
python web_app\production_server.py

echo.
echo 👋 服务器已停止
pause