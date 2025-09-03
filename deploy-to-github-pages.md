# 🚀 JobSpy GitHub Pages 部署指南

## 📋 部署概覽

由於 GitHub Pages 只支援靜態網站，我們採用**混合部署**策略：

- **前端**: GitHub Pages（靜態 HTML/CSS/JS）
- **後端**: 外部平台（Railway/Heroku/Vercel）

## 🎯 快速部署步驟

### 步驟 1: 部署後端 API

#### 選項 A: Railway（推薦）⭐

1. **註冊 Railway**
   - 訪問 [railway.app](https://railway.app)
   - 使用 GitHub 帳號登入

2. **部署專案**
   ```bash
   # 在 Railway 控制台
   # 1. 點擊 "New Project"
   # 2. 選擇 "Deploy from GitHub repo"
   # 3. 選擇你的 jobseeker 倉庫
   # 4. 選擇 web_app 目錄作為根目錄
   ```

3. **設置環境變數**
   ```bash
   SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=False
   HOST=0.0.0.0
   PORT=5000
   ```

4. **獲取部署 URL**
   - Railway 會提供類似 `https://your-app.railway.app` 的 URL
   - 記錄這個 URL，稍後需要配置到前端

#### 選項 B: Heroku

1. **安裝 Heroku CLI**
   ```bash
   # Windows
   winget install Heroku.HerokuCLI
   
   # 或下載安裝包
   # https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **部署**
   ```bash
   # 登入
   heroku login
   
   # 創建應用
   heroku create your-jobspy-app
   
   # 設置環境變數
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set FLASK_DEBUG=False
   
   # 部署
   git push heroku main
   ```

### 步驟 2: 配置前端 API 端點

1. **更新 API 配置**
   
   編輯 `static_frontend/app.js`：
   ```javascript
   const CONFIG = {
       // 替換為你的後端 URL
       API_BASE_URL: 'https://your-app.railway.app',
       // ... 其他配置保持不變
   };
   ```

2. **測試 API 連接**
   ```bash
   # 測試健康檢查端點
   curl https://your-app.railway.app/health
   
   # 應該返回：
   # {"status":"healthy","timestamp":"...","version":"1.0.0"}
   ```

### 步驟 3: 部署到 GitHub Pages

#### 方法 1: 自動部署（推薦）🤖

1. **設置 GitHub Pages**
   - 進入你的 GitHub 倉庫
   - 點擊 "Settings" → "Pages"
   - 選擇 "GitHub Actions" 作為源

2. **添加 Secrets**
   - 進入 "Settings" → "Secrets and variables" → "Actions"
   - 添加以下 Secret：
     ```
     API_BASE_URL: https://your-app.railway.app
     ```

3. **推送代碼**
   ```bash
   git add .
   git commit -m "feat: 添加 GitHub Pages 部署配置"
   git push origin main
   ```

4. **查看部署狀態**
   - 進入 "Actions" 標籤
   - 查看 "Deploy to GitHub Pages" 工作流程
   - 等待部署完成

#### 方法 2: 手動部署

1. **創建 gh-pages 分支**
   ```bash
   git checkout -b gh-pages
   ```

2. **複製靜態文件**
   ```bash
   # 複製靜態前端文件到根目錄
   cp -r static_frontend/* .
   
   # 更新 API 端點
   sed -i "s|https://your-backend.railway.app|https://your-app.railway.app|g" app.js
   ```

3. **提交並推送**
   ```bash
   git add .
   git commit -m "Deploy static frontend to GitHub Pages"
   git push origin gh-pages
   ```

4. **設置 Pages 源**
   - 進入倉庫 "Settings" → "Pages"
   - 選擇 "Deploy from a branch"
   - 選擇 "gh-pages" 分支
   - 選擇 "/ (root)" 作為源目錄

### 步驟 4: 驗證部署

1. **訪問你的網站**
   ```
   https://your-username.github.io/jobseeker
   ```

2. **測試功能**
   - 輸入搜尋關鍵字
   - 點擊搜尋按鈕
   - 檢查是否返回結果

3. **檢查控制台**
   - 打開瀏覽器開發者工具
   - 查看 Console 是否有錯誤
   - 檢查 Network 標籤的 API 請求

## 🔧 進階配置

### 自定義域名

1. **購買域名**
   - 在域名註冊商購買域名
   - 例如：`your-jobspy.com`

2. **設置 DNS**
   ```
   CNAME www your-username.github.io
   CNAME @ your-username.github.io
   ```

3. **添加 CNAME 文件**
   ```bash
   echo "your-jobspy.com" > static_frontend/CNAME
   ```

4. **更新 GitHub Pages 設置**
   - 在倉庫設置中啟用自定義域名
   - 強制 HTTPS

### 環境變數管理

在 GitHub 倉庫設置中添加：

```
API_BASE_URL: https://your-app.railway.app
CUSTOM_DOMAIN: your-jobspy.com
ADMIN_EMAILS: your-email@example.com
```

### 監控和日誌

1. **Railway 監控**
   - 查看 Railway 控制台的日誌
   - 監控 API 使用量和錯誤

2. **GitHub Pages 監控**
   - 查看 GitHub Actions 日誌
   - 監控部署狀態

## 🐛 故障排除

### 常見問題

1. **API 調用失敗 (CORS 錯誤)**
   ```javascript
   // 解決方案：確保後端 CORS 設置正確
   CORS(app, origins=[
       "https://your-username.github.io",
       "https://your-custom-domain.com"
   ])
   ```

2. **404 錯誤**
   - 檢查文件路徑
   - 確認 GitHub Pages 設置正確
   - 檢查 .nojekyll 文件是否存在

3. **樣式不正確**
   - 清除瀏覽器快取
   - 檢查 CSS 文件路徑
   - 確認 Bootstrap CDN 可訪問

4. **部署失敗**
   - 檢查 GitHub Actions 日誌
   - 確認 Secrets 設置正確
   - 檢查文件權限

### 調試技巧

1. **本地測試**
   ```bash
   # 使用 Python 簡單伺服器測試靜態文件
   cd static_frontend
   python -m http.server 8000
   # 訪問 http://localhost:8000
   ```

2. **API 測試**
   ```bash
   # 測試後端 API
   curl -X POST https://your-app.railway.app/search \
        -H "Content-Type: application/json" \
        -d '{"query":"軟體工程師","results_wanted":5}'
   ```

## 📊 性能優化

1. **CDN 加速**
   - 使用 jsDelivr 或 unpkg CDN
   - 啟用 Gzip 壓縮

2. **快取策略**
   - 設置適當的 HTTP 快取標頭
   - 使用 Service Worker 快取

3. **圖片優化**
   - 使用 WebP 格式
   - 實施懶載入

## 🔒 安全性

1. **HTTPS 強制**
   - 確保所有請求使用 HTTPS
   - 設置 HSTS 標頭

2. **API 安全**
   - 實施速率限制
   - 驗證輸入參數
   - 使用 API 金鑰（可選）

## 📈 監控和分析

1. **Google Analytics**
   ```html
   <!-- 添加到 index.html -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
   ```

2. **錯誤追蹤**
   - 使用 Sentry 追蹤 JavaScript 錯誤
   - 監控 API 錯誤率

## 🎉 完成！

部署完成後，你的 JobSpy 將可以通過以下方式訪問：

- **GitHub Pages**: `https://your-username.github.io/jobseeker`
- **自定義域名**: `https://your-jobspy.com`

## 📞 支援

如果遇到問題：

1. 查看 [GitHub Issues](https://github.com/jason660519/jobseeker/issues)
2. 檢查 [Railway 文檔](https://docs.railway.app/)
3. 參考 [GitHub Pages 文檔](https://docs.github.com/en/pages)

---

**恭喜！你的 JobSpy 現在已經成功部署到 GitHub Pages！** 🎊
