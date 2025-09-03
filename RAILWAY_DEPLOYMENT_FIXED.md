# 🚀 Railway 部署修復指南

## 🔍 問題分析

之前的 Railway 部署失敗是因為：

1. **Railway 優先級問題**：Railway 檢測到根目錄的 `Dockerfile`，優先使用 Docker 而不是 `nixpacks.toml`
2. **Dockerfile 問題**：
   - 多階段構建過於複雜
   - 工作目錄設定為 `/app/web_app`，但 Railway 從根目錄構建
   - 沒有使用 Railway 的 `$PORT` 環境變數
3. **nixpacks.toml 配置問題**：依賴安裝路徑不正確

## ✅ 已修復的問題

### 1. 移除 Dockerfile 衝突

- ✅ 將 `Dockerfile` 重命名為 `Dockerfile.local`
- ✅ Railway 現在會使用 `nixpacks.toml` 進行部署

### 2. 修正 nixpacks.toml 配置

- ✅ 更新 Python 版本為 3.11
- ✅ 修正工作目錄為 `/app/web_app`
- ✅ 修正依賴安裝順序：先安裝根目錄的 jobseeker 套件，再安裝 web_app 依賴
- ✅ 添加 Gunicorn 配置參數（workers, timeout）

### 3. 確保 PORT 環境變數正確使用

- ✅ `app.py` 已正確配置 `PORT` 環境變數
- ✅ `Procfile` 已更新 Gunicorn 配置

### 4. 優化 .railwayignore

- ✅ 排除不必要的文件和目錄
- ✅ 減少部署包大小
- ✅ 提高部署速度

## 🚀 部署步驟

### 方法一：從 GitHub 部署（推薦）

1. **提交修復到 GitHub**

   ```bash
   git add .
   git commit -m "fix: 修復 Railway 部署配置

   - 重命名 Dockerfile 為 Dockerfile.local
   - 修正 nixpacks.toml 配置
   - 更新 .railwayignore
   - 優化 Gunicorn 配置"
   git push origin main
   ```

2. **在 Railway 中重新部署**

   - 前往 [railway.app](https://railway.app)
   - 選擇你的 JobSpy 專案
   - 點擊 "Deploy" 或 "Redeploy"
   - Railway 現在會使用 `nixpacks.toml` 而不是 Dockerfile

3. **設定環境變數**
   在 Railway 專案設定中添加：
   ```
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=your-super-secret-key-here
   ```

### 方法二：使用 Railway CLI

1. **安裝 Railway CLI**

   ```bash
   npm install -g @railway/cli
   ```

2. **登入並部署**
   ```bash
   railway login
   cd web_app
   railway up
   ```

## 📋 部署配置說明

### nixpacks.toml 配置

```toml
[start]
cmd = "gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120"

[variables]
PYTHON_VERSION = "3.11"
FLASK_ENV = "production"
FLASK_APP = "app.py"
WORKDIR = "/app/web_app"

[phases.install]
cmds = [
    "pip install --upgrade pip",
    "cd /app && pip install -e .",
    "cd /app/web_app && pip install -r requirements.txt"
]
```

### 關鍵修復點

1. **工作目錄**：設定為 `/app/web_app`
2. **依賴安裝順序**：先安裝 jobseeker 套件，再安裝 web_app 依賴
3. **Gunicorn 配置**：添加 workers 和 timeout 參數
4. **Python 版本**：升級到 3.11

## 🔧 故障排除

### 如果部署仍然失敗

1. **檢查 Railway 構建日誌**

   - 前往 Railway 專案頁面
   - 查看 "Deployments" 標籤
   - 檢查構建日誌中的錯誤訊息

2. **常見問題**

   - **依賴安裝失敗**：檢查 `requirements.txt` 是否包含所有必要套件
   - **模組導入錯誤**：確認 jobseeker 套件正確安裝
   - **端口問題**：確認使用 `$PORT` 環境變數

3. **手動測試**
   ```bash
   # 本地測試 nixpacks 配置
   cd web_app
   pip install -e ..
   pip install -r requirements.txt
   gunicorn app:app --bind 0.0.0.0:5000
   ```

## 📊 部署後驗證

部署成功後，你應該能夠：

1. **訪問應用**：使用 Railway 提供的 URL
2. **測試搜尋功能**：嘗試搜尋職位
3. **檢查 API**：訪問 `/api/sites` 端點
4. **查看日誌**：在 Railway 控制台查看應用日誌

## 🎯 預期結果

修復後，Railway 部署應該：

- ✅ 使用 nixpacks.toml 而不是 Dockerfile
- ✅ 正確安裝所有依賴
- ✅ 成功啟動 Flask 應用
- ✅ 使用 Railway 的 PORT 環境變數
- ✅ 提供穩定的生產環境

## 📞 需要幫助？

如果仍然遇到問題：

1. 檢查 Railway 構建日誌
2. 確認所有文件都已提交到 GitHub
3. 驗證環境變數設定
4. 查看 Railway 官方文檔

---

**修復完成！** 🎉 現在 Railway 應該能夠成功部署你的 JobSpy 應用了。
