# JobSeeker - 多平台職位爬蟲工具

一個強大的 Python 職位搜尋爬蟲工具，支援多個主流求職平台的職位資訊抓取。

## 🚀 功能特色

- **多平台支援**：支援 Indeed、LinkedIn、Glassdoor、Google Jobs、Seek、Naukri、ZipRecruiter、Bayt、BDJobs 等主流求職網站
- **靈活搜尋**：支援關鍵字、地點、薪資範圍等多種搜尋條件
- **資料格式化**：統一的資料結構，便於後續處理和分析
- **高效能**：使用異步處理和智能重試機制
- **易於擴展**：模組化設計，輕鬆添加新的求職平台

## 📦 安裝指南

### 🔧 前置需求

在開始安裝之前，請確保您的電腦已安裝：
- **Python 3.8 或更新版本** - [下載 Python](https://www.python.org/downloads/)
- **Git** - [下載 Git](https://git-scm.com/downloads)（用於下載專案）

### 方法一：使用 uv（最簡單，推薦新手）

1. **安裝 uv 工具**
   ```bash
   # Windows 用戶
   pip install uv
   
   # 或使用 PowerShell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. **下載並安裝 JobSeeker**
   ```bash
   # 下載專案
   git clone https://github.com/jason660519/jobseeker.git
   cd jobseeker
   
   # 創建虛擬環境
   uv venv
   
   # 啟動虛擬環境（Windows）
   .venv\Scripts\activate
   
   # 安裝專案和所有依賴
   uv pip install -e .
   uv pip install playwright
   
   # 安裝瀏覽器驅動（用於 Seek 等平台）
   playwright install
   ```

### 方法二：使用 Poetry（進階用戶）

1. **安裝 Poetry**
   ```bash
   # Windows 用戶
   pip install poetry
   ```

2. **下載並安裝 JobSeeker**
   ```bash
   # 下載專案
   git clone https://github.com/jason660519/jobseeker.git
   cd jobseeker
   
   # 安裝依賴
   poetry install
   
   # 啟動虛擬環境
   poetry shell
   
   # 安裝額外依賴
   poetry add playwright
   playwright install
   ```

### 方法三：使用 pip（傳統方式）

```bash
# 下載專案
git clone https://github.com/jason660519/jobseeker.git
cd jobseeker

# 建議先創建虛擬環境
python -m venv venv
venv\Scripts\activate  # Windows
# 或 source venv/bin/activate  # macOS/Linux

# 安裝依賴
pip install -e .
pip install playwright
playwright install
```

### ✅ 驗證安裝

安裝完成後，執行以下命令測試是否成功：

```python
python -c "from jobspy import scrape_jobs; print('JobSeeker 安裝成功！')"
```

如果看到「JobSeeker 安裝成功！」訊息，表示安裝完成！

## 🔧 使用方法

### 基本使用

```python
from jobspy import scrape_jobs

# 搜尋職位
jobs = scrape_jobs(
    site_name="indeed",
    search_term="python developer",
    location="台北",
    results_wanted=50
)

# 輸出到 CSV
jobs.to_csv("jobs.csv", index=False)
print(f"找到 {len(jobs)} 個職位")
```

### 多平台搜尋

```python
from jobspy import scrape_jobs

# 同時搜尋多個平台
platforms = ["indeed", "linkedin", "glassdoor"]
all_jobs = []

for platform in platforms:
    jobs = scrape_jobs(
        site_name=platform,
        search_term="data scientist",
        location="新北",
        results_wanted=30
    )
    all_jobs.append(jobs)

# 合併結果
import pandas as pd
combined_jobs = pd.concat(all_jobs, ignore_index=True)
combined_jobs.to_csv("all_platform_jobs.csv", index=False)
```

### 進階搜尋選項

```python
jobs = scrape_jobs(
    site_name="seek",
    search_term="software engineer",
    location="Sydney",
    results_wanted=100,
    hours_old=24,  # 只搜尋 24 小時內的職位
    country_indeed="Australia",
    job_type="fulltime",
    is_remote=True
)
```

## 🌐 支援平台

| 平台 | 網站 | 支援地區 |
|------|------|----------|
| Indeed | indeed.com | 全球 |
| LinkedIn | linkedin.com | 全球 |
| Glassdoor | glassdoor.com | 美國、加拿大、英國等 |
| Google Jobs | google.com/jobs | 全球 |
| Seek | seek.com.au | 澳洲、紐西蘭 |
| Naukri | naukri.com | 印度 |
| ZipRecruiter | ziprecruiter.com | 美國 |
| Bayt | bayt.com | 中東地區 |
| BDJobs | bdjobs.com | 孟加拉 |

## 📊 資料結構

爬取的職位資料包含以下欄位：

```python
{
    'title': '職位名稱',
    'company': '公司名稱',
    'location': '工作地點',
    'job_url': '職位連結',
    'job_url_direct': '直接申請連結',
    'description': '職位描述',
    'date_posted': '發布日期',
    'salary_min': '最低薪資',
    'salary_max': '最高薪資',
    'salary_currency': '薪資幣別',
    'job_type': '工作類型',
    'is_remote': '是否遠端工作',
    'site': '來源網站'
}
```

## ⚙️ 配置選項

### 環境變數

```bash
# 設置代理（可選）
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=https://proxy.example.com:8080

# 設置用戶代理（可選）
export USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### 自定義配置

```python
from jobspy import scrape_jobs

# 自定義請求頭
custom_headers = {
    'User-Agent': 'Your Custom User Agent',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
}

jobs = scrape_jobs(
    site_name="indeed",
    search_term="python",
    location="台北",
    headers=custom_headers
)
```

## 🛠️ 開發

### 添加新平台

1. 在 `jobspy/` 目錄下創建新的平台目錄
2. 實作 `__init__.py`、`constant.py` 和 `util.py`
3. 在主要的 `__init__.py` 中註冊新平台

### 運行測試

```bash
# 安裝開發依賴
poetry install --with dev

# 運行測試
pytest tests/

# 運行特定平台測試
pytest tests/test_indeed.py
```

## 📝 注意事項

- **遵守網站條款**：請確保您的使用符合各網站的服務條款
- **合理使用**：避免過於頻繁的請求，建議添加適當的延遲
- **資料準確性**：爬取的資料可能因網站結構變更而受影響
- **法律責任**：使用者需自行承擔使用本工具的法律責任

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

1. Fork 本專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

感謝所有為開源社群貢獻的開發者們！

---

**免責聲明**：本工具僅供學習和研究使用，使用者需自行確保符合相關網站的使用條款和當地法律法規。