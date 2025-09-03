# JobSpy 靜態前端

這是 JobSpy 的靜態前端版本，專為 GitHub Pages 部署設計。

## 🚀 快速開始

### 1. 後端部署

首先需要將 Flask 後端部署到支援 Python 的平台：

#### 選項 A: Railway（推薦）
```bash
# 1. 註冊 Railway 帳號
# 2. 連接 GitHub 倉庫
# 3. 設置環境變數
# 4. 自動部署
```

#### 選項 B: Heroku
```bash
# 1. 安裝 Heroku CLI
# 2. 創建 Heroku 應用
heroku create your-app-name
# 3. 部署
git push heroku main
```

#### 選項 C: Vercel
```bash
# 1. 安裝 Vercel CLI
npm i -g vercel
# 2. 部署
vercel --prod
```

### 2. 配置 API 端點

在 `app.js` 中更新 API 基礎 URL：

```javascript
const CONFIG = {
    // 替換為你的後端 URL
    API_BASE_URL: 'https://your-backend.railway.app',
    // ... 其他配置
};
```

### 3. GitHub Pages 部署

#### 方法 1: 自動部署（推薦）

1. 進入 GitHub 倉庫設置
2. 選擇 "Pages" 選項
3. 選擇 "GitHub Actions" 作為源
4. 推送代碼到 main 分支
5. GitHub Actions 會自動構建和部署

#### 方法 2: 手動部署

1. 創建 gh-pages 分支：
```bash
git checkout -b gh-pages
```

2. 複製靜態文件到根目錄：
```bash
cp -r static_frontend/* .
```

3. 提交並推送：
```bash
git add .
git commit -m "Deploy static frontend"
git push origin gh-pages
```

4. 在 GitHub 設置中選擇 gh-pages 分支作為源

## 🔧 配置說明

### 環境變數

在 GitHub 倉庫設置中添加以下 Secrets：

- `API_BASE_URL`: 後端 API 的完整 URL
- `CUSTOM_DOMAIN`: 自定義域名（可選）

### CORS 設置

確保後端正確配置 CORS：

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "https://your-username.github.io",
    "https://your-custom-domain.com"
])
```

## 📁 文件結構

```
static_frontend/
├── index.html          # 主頁面
├── styles.css          # 樣式文件
├── app.js             # JavaScript 邏輯
└── README.md          # 說明文檔
```

## 🎨 自定義

### 修改樣式

編輯 `styles.css` 文件來自定義外觀：

```css
:root {
    --primary-color: #your-color;
    --gradient-primary: linear-gradient(135deg, #color1, #color2);
}
```

### 添加功能

在 `app.js` 中添加新的功能：

```javascript
// 添加新的 API 端點
async function newFeature() {
    const response = await fetch(`${CONFIG.API_BASE_URL}/new-endpoint`);
    // 處理響應
}
```

## 🔍 功能特色

- ✅ 響應式設計
- ✅ 多平台搜尋
- ✅ 即時結果展示
- ✅ 分頁功能
- ✅ 下載支援
- ✅ 鍵盤快捷鍵
- ✅ 無障礙設計
- ✅ 快取機制

## 🐛 故障排除

### 常見問題

1. **API 調用失敗**
   - 檢查 `API_BASE_URL` 配置
   - 確認後端服務運行正常
   - 檢查 CORS 設置

2. **樣式不正確**
   - 清除瀏覽器快取
   - 檢查 CSS 文件路徑
   - 確認 Bootstrap CDN 可訪問

3. **JavaScript 錯誤**
   - 打開瀏覽器開發者工具
   - 檢查 Console 錯誤訊息
   - 確認 API 響應格式正確

### 調試模式

在 `app.js` 中啟用調試模式：

```javascript
const CONFIG = {
    DEBUG: true,  // 啟用調試模式
    // ... 其他配置
};
```

## 📊 性能優化

- 使用 CDN 載入外部資源
- 壓縮 CSS 和 JavaScript
- 啟用瀏覽器快取
- 使用圖片優化
- 實施懶載入

## 🔒 安全性

- 使用 HTTPS
- 驗證 API 響應
- 防止 XSS 攻擊
- 限制 API 調用頻率

## 📈 監控

建議添加以下監控：

- Google Analytics
- 錯誤追蹤（如 Sentry）
- 性能監控
- API 使用統計

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

開源專案，MIT 授權。

## 📞 支援

如有問題，請：

1. 查看文檔
2. 搜索現有 Issue
3. 創建新的 Issue
4. 聯繫維護者
