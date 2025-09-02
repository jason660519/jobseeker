# jobseeker 網頁應用

🚀 **智能職位搜尋平台** - 為一般民眾提供簡單易用的網頁界面，無需程式設計知識即可使用 jobseeker 的強大功能。

## ✨ 功能特色

### 🎯 核心功能
- **智能搜尋**: 使用 AI 技術從多個求職平台搜尋職位
- **全球覆蓋**: 支援 50+ 個求職網站，覆蓋 100+ 個國家
- **即時結果**: AJAX 支援的動態搜尋，無需頁面重載
- **多格式下載**: 支援 CSV 和 JSON 格式下載搜尋結果
- **響應式設計**: 完美支援桌面、平板和手機設備

### 🛠 技術特色
- **Flask 框架**: 輕量級、高效能的 Python Web 框架
- **Bootstrap 5**: 現代化的響應式 UI 設計
- **RESTful API**: 標準化的 API 接口設計
- **Docker 支援**: 容器化部署，易於擴展
- **生產就緒**: 支援 Gunicorn WSGI 伺服器

## 📋 系統需求

- **Python**: 3.8 或更高版本
- **作業系統**: Windows, macOS, Linux
- **記憶體**: 建議 2GB 或以上
- **磁碟空間**: 至少 1GB 可用空間

## 🚀 快速開始

### 1. 安裝 jobseeker 套件

首先確保已安裝 jobseeker 核心套件：

```bash
# 切換到專案根目錄
cd /path/to/JobSpy

# 安裝 jobseeker 套件
pip install -e .

# 安裝 Playwright（用於網頁爬取）
pip install playwright
playwright install
```

### 2. 安裝網頁應用依賴

```bash
# 切換到網頁應用目錄
cd web_app

# 安裝依賴套件
pip install -r requirements.txt
```

### 3. 啟動應用

#### 方法一：使用啟動腳本（推薦）

```bash
# 開發模式（啟用除錯和自動重載）
python run.py --mode dev

# 生產模式（使用 Gunicorn）
python run.py --mode prod

# 自定義端口
python run.py --mode dev --port 8080

# 查看所有選項
python run.py --help
```

#### 方法二：直接啟動 Flask

```bash
# 開發模式
python app.py

# 或使用 Flask 命令
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

### 4. 訪問應用

開啟瀏覽器，訪問：
- **本地訪問**: http://localhost:5000
- **網路訪問**: http://your-ip:5000

## 🐳 Docker 部署

### 創建 Docker 檔案

```bash
# 創建 Dockerfile 和 docker-compose.yml
python run.py --create-docker
```

### 使用 Docker Compose 啟動

```bash
# 建置並啟動容器
docker-compose up --build

# 背景執行
docker-compose up -d --build

# 停止容器
docker-compose down
```

### 手動 Docker 建置

```bash
# 建置映像
docker build -t jobseeker-web .

# 執行容器
docker run -p 5000:5000 jobseeker-web
```

## 📖 使用指南

### 基本搜尋

1. **輸入關鍵字**: 在「職位關鍵字」欄位輸入您要搜尋的職位，例如：
   - `軟體工程師`
   - `數據分析師`
   - `產品經理`
   - `Python Developer`

2. **設定地點**（可選）: 輸入工作地點，例如：
   - `台北`
   - `新竹`
   - `遠端工作`
   - `Remote`

3. **選擇結果數量**: 從下拉選單選擇要搜尋的職位數量（20、50 或 100）

4. **設定時間限制**（可選）: 選擇職位發布的時間範圍

5. **開始搜尋**: 點擊「開始智能搜尋」按鈕

### 查看結果

搜尋完成後，您將看到：

- **統計資訊**: 找到的職位總數、成功的平台數量、信心指數和搜尋時間
- **職位列表**: 詳細的職位資訊，包括：
  - 職位標題和公司名稱
  - 工作地點和薪資範圍
  - 職位描述和發布時間
  - 職位類型和是否支援遠端工作
  - 直接連結到原始職位頁面

### 下載結果

- **CSV 格式**: 適合在 Excel 或其他試算表軟體中開啟
- **JSON 格式**: 適合程式開發者進一步處理數據

## 🔧 配置選項

### 環境變數

您可以通過環境變數自定義應用行為：

```bash
# Flask 配置
export FLASK_ENV=production          # 運行環境（development/production）
export FLASK_DEBUG=false             # 除錯模式
export SECRET_KEY=your-secret-key     # 應用密鑰

# 伺服器配置
export PORT=5000                      # 伺服器端口
export HOST=0.0.0.0                   # 伺服器主機

# jobseeker 配置
export JOBSEEKER_TIMEOUT=120          # 搜尋超時時間（秒）
export JOBSEEKER_MAX_RESULTS=100      # 最大搜尋結果數

# LLM 解析（可選）
export ENABLE_LLM_PARSER=true         # 啟用單欄查詢的 LLM 解析
export LLM_PROVIDER=openai            # 目前支援 openai
export OPENAI_API_KEY=sk-...          # 你的 OpenAI API 金鑰
export OPENAI_BASE_URL=https://api.openai.com/v1  # 非必要，預設如左
export LLM_MODEL=gpt-4o-mini          # 建議小模型以獲得低延遲
```

### 自定義配置檔案

創建 `.env` 檔案來設定環境變數：

```env
# .env 檔案
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-very-secret-key-here
PORT=5000
HOST=0.0.0.0
```

## 🛡 安全性考量

### 生產環境部署

1. **設定強密鑰**:
   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **停用除錯模式**:
   ```bash
   export FLASK_DEBUG=false
   export FLASK_ENV=production
   ```

3. **使用反向代理**: 建議在生產環境中使用 Nginx 或 Apache 作為反向代理

4. **HTTPS 支援**: 配置 SSL/TLS 憑證以啟用 HTTPS

### 防火牆設定

確保只開放必要的端口：
```bash
# 允許 HTTP 流量
sudo ufw allow 5000/tcp

# 允許 HTTPS 流量（如果使用）
sudo ufw allow 443/tcp
```

## 📊 API 文檔

### 搜尋 API

**端點**: `POST /search`

**請求格式**:
```json
{
  "query": "軟體工程師",
  "location": "台北",
  "results_wanted": 20,
  "hours_old": 72
}
```

**響應格式**:
```json
{
  "success": true,
  "search_id": "uuid-string",
  "total_jobs": 25,
  "jobs": [...],
  "routing_info": {
    "successful_agents": ["indeed", "linkedin"],
    "confidence_score": 0.85,
    "execution_time": 15.2
  }
}
```

### 下載 API

**端點**: `GET /download/<search_id>/<format>`

- `search_id`: 搜尋 ID
- `format`: 下載格式（`csv` 或 `json`）

### 健康檢查 API

**端點**: `GET /health`

**響應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0"
}
```

## 🔍 故障排除

### 常見問題

#### 1. 無法啟動應用

**錯誤**: `ModuleNotFoundError: No module named 'jobseeker'`

**解決方案**:
```bash
# 確保已安裝 jobseeker 套件
cd /path/to/JobSpy
pip install -e .
```

#### 2. 搜尋失敗

**錯誤**: `搜尋過程中發生錯誤`

**可能原因**:
- 網路連線問題
- Playwright 瀏覽器未安裝
- 目標網站暫時無法訪問

**解決方案**:
```bash
# 重新安裝 Playwright 瀏覽器
playwright install

# 檢查網路連線
ping google.com
```

#### 3. 端口被佔用

**錯誤**: `Address already in use`

**解決方案**:
```bash
# 使用不同端口
python run.py --mode dev --port 8080

# 或終止佔用端口的進程
lsof -ti:5000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5000   # Windows
```

### 日誌檢查

啟用詳細日誌以診斷問題：

```bash
# 設定日誌級別
export FLASK_DEBUG=true

# 啟動應用並查看詳細輸出
python run.py --mode dev
```

## 🤝 貢獻指南

我們歡迎社群貢獻！請遵循以下步驟：

1. **Fork 專案**
2. **創建功能分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **創建 Pull Request**

### 開發環境設定

```bash
# 克隆專案
git clone https://github.com/your-username/JobSpy.git
cd JobSpy

# 安裝開發依賴
pip install -e ".[dev]"

# 安裝網頁應用依賴
cd web_app
pip install -r requirements.txt

# 啟動開發伺服器
python run.py --mode dev
```

### 程式碼風格

- 使用 **Black** 進行程式碼格式化
- 使用 **flake8** 進行程式碼檢查
- 遵循 **PEP 8** 編碼規範
- 添加適當的註釋和文檔字串

## 📄 授權條款

本專案採用 MIT 授權條款。詳細資訊請參閱 [LICENSE](../LICENSE) 檔案。

## 🙏 致謝

- **jobseeker 團隊**: 提供強大的職位搜尋核心功能
- **Flask 社群**: 優秀的 Web 框架
- **Bootstrap 團隊**: 美觀的 UI 組件庫
- **所有貢獻者**: 感謝每一位為專案做出貢獻的開發者

## 📞 聯絡我們

- **GitHub Issues**: [提交問題或建議](https://github.com/your-username/JobSpy/issues)
- **電子郵件**: support@jobseeker.com
- **官方網站**: https://jobseeker.com

---

**🚀 立即開始使用 jobseeker 網頁應用，讓找工作變得更簡單！**
