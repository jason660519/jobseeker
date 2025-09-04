@echo off
REM LiteLLM Docker 代理服務器啟動腳本
REM 用於快速部署和測試LiteLLM代理服務器

echo ============================================================
echo 🐳 LiteLLM Docker 代理服務器啟動腳本
echo ============================================================
echo.

REM 檢查Docker是否安裝
echo 🔍 檢查Docker安裝狀態...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安裝或未啟動
    echo 💡 請先安裝Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker已安裝

REM 檢查Docker Compose是否可用
echo 🔍 檢查Docker Compose...
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose不可用
    echo 💡 請確保Docker Desktop正在運行
    pause
    exit /b 1
)
echo ✅ Docker Compose可用

REM 檢查配置文件
echo 🔍 檢查配置文件...
if not exist "litellm_config.yaml" (
    echo ❌ 找不到litellm_config.yaml配置文件
    echo 💡 請確保配置文件存在於當前目錄
    pause
    exit /b 1
)
echo ✅ 配置文件存在

REM 設置環境變量
echo 🔧 設置環境變量...
if "%OPENAI_API_KEY%"=="" (
    echo ⚠️  OPENAI_API_KEY 未設置
) else (
    echo ✅ OPENAI_API_KEY 已設置
)

if "%ANTHROPIC_API_KEY%"=="" (
    echo ⚠️  ANTHROPIC_API_KEY 未設置
) else (
    echo ✅ ANTHROPIC_API_KEY 已設置
)

if "%DEEPSEEK_API_KEY%"=="" (
    echo ⚠️  DEEPSEEK_API_KEY 未設置
) else (
    echo ✅ DEEPSEEK_API_KEY 已設置
)

echo.
echo 🚀 啟動LiteLLM代理服務器...
echo 📍 配置文件: litellm_config.yaml
echo 🌐 服務地址: http://localhost:4000
echo 📚 API文檔: http://localhost:4000/docs
echo.

REM 啟動Docker Compose
docker compose -f docker-compose.litellm.yml up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ LiteLLM代理服務器啟動成功！
    echo.
    echo 🔗 可用端點:
    echo    • 健康檢查: http://localhost:4000/health
    echo    • 模型列表: http://localhost:4000/v1/models
    echo    • 聊天完成: http://localhost:4000/v1/chat/completions
    echo    • Web UI: http://localhost:4000
    echo.
    echo 🧪 運行測試腳本:
    echo    python test_litellm_docker.py
    echo.
    echo 🛑 停止服務:
    echo    docker compose -f docker-compose.litellm.yml down
    echo.
) else (
    echo ❌ 啟動失敗，請檢查錯誤信息
)

echo ============================================================
pause