# Railway 部署指南

這份指南將幫助你將 JobSpy Flask 網頁應用部署到 Railway 平台。

## 📋 部署前準備

### 1. 確認檔案結構
確保你的 `web_app` 目錄包含以下檔案：
```
web_app/
├── app.py                 # 主應用檔案
├── requirements.txt       # Python 依賴套件
├── nixpacks.toml         # Railway 構建配置
├── Procfile              # 備用啟動配置
├── .env.example          # 環境變數範例
├── templates/            # HTML 模板
├── static/               # 靜態檔案
└── db/                   # 資料庫目錄
```

### 2. 檢查依賴套件
確認 `requirements.txt` 包含所有必要的套件，特別是：
- Flask 相關套件
- Gunicorn（生產伺服器）
- jobseeker 核心依賴

## 🚀 Railway 部署步驟

### 方法一：從 GitHub 部署（推薦）

1. **推送代碼到 GitHub**
   ```bash
   git add .
   git commit -m "feat: 準備 Railway 部署配置"
   git push origin main
   ```

2. **登入 Railway**
   - 前往 [railway.app](https://railway.app)
   - 使用 GitHub 帳號登入

3. **創建新專案**
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇你的 JobSpy 倉庫

4. **配置部署設定**
   - Railway 會自動檢測到這是 Python 專案
   - 確認根目錄設定為 `web_app`
   - Railway 會使用 `nixpacks.toml` 進行構建

5. **設定環境變數**
   在 Railway 專案設定中添加：
   ```
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=your-super-secret-key-here
   ```

6. **部署**
   - 點擊 "Deploy"
   - 等待構建完成
   - 獲取公開 URL

### 方法二：使用 Railway CLI

1. **安裝 Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **登入 Railway**
   ```bash
   railway login
   ```

3. **初始化專案**
   ```bash
   cd web_app
   railway init
   ```

4. **部署**
   ```bash
   railway up
   ```

## ⚙️ 配置說明

### nixpacks.toml
這個檔案告訴 Railway 如何構建和啟動你的應用：
- 使用 Gunicorn 作為生產伺服器
- 設定 Python 版本為 3.10
- 配置環境變數

### Procfile
備用配置檔案，如果 Railway 不使用 nixpacks.toml 時會使用這個。

### requirements.txt
包含所有必要的 Python 套件，已經針對 Railway 部署進行優化。

## 🔧 常見問題

### 1. 構建失敗
- 檢查 `requirements.txt` 是否包含所有依賴
- 確認 Python 版本兼容性
- 查看 Railway 構建日誌

### 2. 應用無法啟動
- 確認 `app.py` 中的端口配置正確
- 檢查環境變數設定
- 查看應用日誌

### 3. 資料庫問題
- SQLite 資料庫會在首次啟動時自動創建
- 如需持久化資料，考慮使用 Railway 的 PostgreSQL 服務

### 4. 靜態檔案問題
- 確認 `static` 和 `templates` 目錄已包含在倉庫中
- 檢查檔案路徑是否正確

## 📊 監控和維護

### 查看日誌
```bash
railway logs
```

### 查看部署狀態
```bash
railway status
```

### 重新部署
```bash
railway up --detach
```

## 💰 費用說明

- Railway 提供每月 $5 免費額度
- 對於小型專案通常足夠使用
- 超出額度後按使用量計費

## 🔗 有用連結

- [Railway 官方文檔](https://docs.railway.app/)
- [Flask 部署指南](https://docs.railway.app/guides/flask)
- [Railway 定價](https://railway.app/pricing)

## 🆘 需要幫助？

如果遇到問題，可以：
1. 查看 Railway 官方文檔
2. 檢查 Railway 社群論壇
3. 查看專案的 GitHub Issues

---

祝你部署順利！🎉