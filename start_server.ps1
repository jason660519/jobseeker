# JobSpy 網頁服務器啟動腳本
# 支援本地和網路訪問

Write-Host "🚀 啟動 JobSpy 網頁服務器" -ForegroundColor Green
Write-Host ""

# 檢查虛擬環境
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✅ 找到虛擬環境，正在啟動..." -ForegroundColor Green
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  未找到虛擬環境，使用系統 Python" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🌐 啟動網頁應用..." -ForegroundColor Cyan
Write-Host "📱 本地訪問: http://127.0.0.1:5000" -ForegroundColor White
Write-Host "📱 網路訪問: http://192.168.1.181:5000" -ForegroundColor White
Write-Host "📊 API 文檔: http://127.0.0.1:5000/api/sites" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服務器" -ForegroundColor Yellow
Write-Host ""

# 切換到 web_app 目錄並啟動
Set-Location web_app
try {
    python app.py
} catch {
    Write-Host "❌ 啟動失敗: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "👋 服務器已停止" -ForegroundColor Green
    Set-Location ..
}

Read-Host "按 Enter 鍵退出"