# 🔍 JobSpy - 智能職位搜尋工具

> **一個強大且易用的 Python 職位搜尋工具，讓找工作變得更簡單！**

無論您是求職者、HR、還是數據分析師，JobSpy 都能幫您快速從全球主流求職網站搜集職位資訊。只需一行指令，就能搜尋數百個職位！

## 🚨 **重要部署建議**

### 💡 **強烈推薦：本地安裝使用**

我們強烈建議您在本地電腦安裝使用 JobSpy，而不是使用雲端部署版本。原因如下：

#### ✅ **本地部署優勢**
- 🚀 **即時響應**：無冷啟動延遲，立即開始搜尋
- 💪 **完整效能**：使用您電腦的全部 CPU 和記憶體資源
- 🔒 **隱私保護**：所有搜尋在本地處理，無需上傳資料到伺服器
- 💰 **零成本**：無需支付雲端運算費用
- 🛡️ **穩定性**：不受網路連線或伺服器問題影響

#### ⚠️ **雲端部署問題警告**
- ⏰ **長時間等待**：冷啟動可能需要 5-15 秒甚至更久
- 🐌 **效能限制**：伺服器資源受限，搜尋速度較慢
- 💸 **成本問題**：每月伺服器費用 $5-20
- 🔌 **依賴性**：需要穩定網路連線才能正常使用
- 📊 **資源競爭**：與其他使用者共享伺服器資源

### 🚀 **未來發展：全新客戶端解決方案**

我們正在開發下一代 JobSpy 生態系統，完全擺脫伺服器依賴，提供更優秀的使用體驗：

#### 📱 **即將推出的解決方案**
- 🖥️ **桌面應用程式**：Electron + Python，一鍵安裝，離線使用
- 🌐 **瀏覽器擴充功能**：Chrome/Firefox 外掛，直接在求職網站增強功能
- 📱 **漸進式網頁應用 (PWA)**：手機和平板電腦專用，支援離線搜尋
- 🏢 **企業版本**：團隊管理、批量搜尋、進階分析功能

#### 💰 **可持續的商業模式**
- 🆓 **免費版本**：基本搜尋功能，滿足個人求職需求
- 💎 **專業版本**：進階功能、無限搜尋、匯出功能
- 🚀 **訂閱服務**：即時薪資分析、公司評價、市場趨勢

### 📋 **參與我們的遷移計劃**

> **🔗 了解詳情**：查看我們完整的 [遷移計劃文件](./migration_plans/) 了解技術架構、商業模式和實施時程。

#### 🤝 **如何參與貢獻**
- 💡 **提供建議**：分享您對新功能的想法和需求
- 🧪 **測試體驗**：參與 Beta 版本測試，提供使用回饋
- 👨‍💻 **程式開發**：貢獻程式碼，加速開發進度
- 📣 **推廣宣傳**：幫助更多人了解和使用 JobSpy
- 💰 **資金支持**：支持我們持續改進和創新

#### 📅 **開發時程**
- **第一階段 (2-3個月)**：桌面應用程式 Beta 版
- **第二階段 (3-4個月)**：付費功能和訂閱服務
- **第三階段 (5-6個月)**：瀏覽器擴充功能和企業版

> **⏰ 保持耐心**：優質軟體需要時間開發和測試。在此期間，我們建議您使用本地安裝版本，獲得最佳使用體驗！

## ✨ 為什麼選擇 JobSpy？

### 🧠 **智能路由系統** - 自動選擇最佳搜尋策略
- 根據您的查詢自動選擇最適合的求職網站
- 支援中文、英文等多語言查詢
- 智能識別地理位置和行業類型

### 🌍 **全球求職網站支援**
- **歐洲**：Indeed、LinkedIn、Glassdoor、Google Jobs
- **澳洲**：Seek、Indeed、LinkedIn
- **美國**：ZipRecruiter、Indeed、LinkedIn、Glassdoor
- **亞洲**：Naukri（印度）、BDJobs（孟加拉）
- **中東**：Bayt

### 📊 **完整的搜尋報告**
- 詳細的代理使用報告
- 搜尋成功率統計
- 職位來源分析
- 搜尋結果品質評估

### 🚀 **簡單易用**
- 一行指令完成搜尋
- 自動輸出 CSV 檔案
- 支援命令列和 Python 程式
- 詳細的使用範例

## 📦 安裝指南

### 🔧 前置需求

在開始安裝之前，請確保您的電腦已安裝：
- **Python 3.10 或更新版本** - [下載 Python](https://www.python.org/downloads/)
- **Git** - [下載 Git](https://git-scm.com/downloads)（用於下載專案）

> 💡 **為什麼選擇本地安裝？**
> - 🚀 **即時響應**：無冷啟動延遲，立即開始搜尋
> - 💪 **完整功能**：使用您電腦的全部 CPU 和記憶體資源
> - 🔒 **隱私保護**：所有搜尋在本地處理，無需上傳資料
> - 💰 **零成本**：無需支付雲端運算費用

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
python -c "from jobseeker import scrape_jobs; print('JobSpy 安裝成功！')"
```

如果看到「JobSpy 安裝成功！」訊息，表示安裝完成！

## 🚀 快速開始 - 3 分鐘學會使用

### 📱 **方法一：命令列搜尋（最簡單）**

```bash
# 基本搜尋 - 只需要一行指令！
python smart_job_search.py "我想找台北的軟體工程師工作"

# 搜尋特定數量的職位
python smart_job_search.py "尋找新加坡的資料科學家職位" --results 50

# 只搜尋最近 24 小時的職位
python smart_job_search.py "Looking for marketing jobs in London" --hours 24

# 儲存結果到指定檔案
python smart_job_search.py "Find AI engineer jobs in Berlin" --output my_jobs.csv
```

### 🐍 **方法二：Python 程式搜尋**

```python
from jobseeker.route_manager import smart_scrape_jobs

# 智能搜索 - 系統會自動選擇最適合的求職網站
result = smart_scrape_jobs(
    user_query="請你幫我找歐洲地區的 AI 工程師工作",
    results_wanted=30
)

# 查看搜尋結果摘要
print(f"✅ 總共找到 {result.total_jobs} 個職位")
print(f"🤖 使用的求職網站: {[a.value for a in result.successful_agents]}")
print(f"📊 搜尋信心度: {result.confidence_score:.2f}")

# 儲存職位資料
if result.combined_jobs_data is not None:
    result.combined_jobs_data.to_csv("歐洲_AI工程師_職位.csv", index=False)
    print(f"💾 職位資料已儲存到 '歐洲_AI工程師_職位.csv'")
```

## 📊 如何理解搜尋結果

### 🎯 **搜尋結果檔案說明**

當您執行搜尋後，jobseeker 會產生以下檔案：

```
📁 搜尋結果資料夾/
├── 📄 歐洲_AI工程師_職位.csv          # 主要職位資料
├── 📄 搜尋報告_20240902_033230.txt    # 詳細搜尋報告
└── 📄 代理使用統計.json              # 代理效能分析
```

### 📋 **職位資料 CSV 檔案內容**

每個職位包含以下重要資訊：

| 欄位名稱 | 說明 | 範例 |
|---------|------|------|
| `title` | 職位名稱 | "Senior AI Engineer" |
| `company` | 公司名稱 | "Google" |
| `location` | 工作地點 | "London, UK" |
| `job_url` | 職位連結 | 可直接點擊查看詳情 |
| `job_url_direct` | 直接申請連結 | 可直接申請工作 |
| `description` | 職位描述 | 詳細的工作內容和要求 |
| `date_posted` | 發布日期 | "2024-09-02" |
| `salary_min` | 最低薪資 | 50000 |
| `salary_max` | 最高薪資 | 80000 |
| `salary_currency` | 薪資幣別 | "GBP" |
| `site` | 來源網站 | "indeed" |

### 📈 **如何分析搜尋結果品質**

```python
import pandas as pd

# 讀取搜尋結果
jobs = pd.read_csv("歐洲_AI工程師_職位.csv")

# 基本統計
print(f"📊 總職位數: {len(jobs)}")
print(f"🏢 涉及公司數: {jobs['company'].nunique()}")
print(f"🌍 涉及城市數: {jobs['location'].nunique()}")
print(f"💰 有薪資資訊的職位: {jobs['salary_min'].notna().sum()}")

# 來源網站分布
print("\n📱 職位來源分布:")
print(jobs['site'].value_counts())

# 熱門公司
print("\n🏆 熱門招聘公司:")
print(jobs['company'].value_counts().head(10))
```

## 🤖 代理報告詳解 - 了解搜尋策略

### 📋 **什麼是代理報告？**

jobseeker 的智能路由系統會為每次搜尋產生詳細的代理使用報告，幫您了解：
- 🎯 **哪些求職網站被選中**（啟用的代理）
- ❌ **哪些求職網站未被使用**（未啟用的代理）
- 📊 **每個網站的搜尋效果**
- 🧠 **系統的決策邏輯**

### 📊 **代理報告範例解讀**

```
=== jobseeker 智能路由報告 ===
搜尋查詢: "歐洲地區 AI 工程師職位"
執行時間: 2024-09-02 03:32:30

🎯 路由決策:
├─ 識別地理區域: Europe (信心度: 1.00)
├─ 識別行業類型: Technology (信心度: 1.00)
└─ 選擇策略: 歐洲科技職位專用

✅ 啟用的代理 (4個):
├─ 🥇 LinkedIn    │ 主要代理 │ 找到 18 個職位 │ 成功率 100%
├─ 🥈 Indeed     │ 主要代理 │ 找到 15 個職位 │ 成功率 100%
├─ 🥉 Glassdoor  │ 次要代理 │ 找到 8 個職位  │ 成功率 100%
└─ 🏅 Google Jobs │ 次要代理 │ 找到 5 個職位  │ 成功率 100%

❌ 未啟用的代理 (5個):
├─ Seek         │ 原因: 僅適用於澳洲/紐西蘭地區
├─ ZipRecruiter │ 原因: 主要服務美國市場
├─ Naukri       │ 原因: 專門服務印度市場
├─ Bayt         │ 原因: 專門服務中東地區
└─ BDJobs       │ 原因: 專門服務孟加拉市場

📈 搜尋統計:
├─ 總職位數: 46 個
├─ 平均信心度: 0.90
├─ 路由成功率: 100%
└─ 搜尋耗時: 45.2 秒
```

### 🎯 **智能路由決策邏輯**

| 查詢範例 | 啟用的代理 | 未啟用的代理 | 決策原因 |
|----------|------------|--------------|----------|
| "歐洲 AI 工程師" | LinkedIn, Indeed, Glassdoor, Google | Seek, ZipRecruiter, Naukri, Bayt, BDJobs | 地理匹配 + 科技行業專長 |
| "澳洲建築工作" | Seek, Indeed, LinkedIn | ZipRecruiter, Naukri, Bayt, BDJobs, Glassdoor | 澳洲地區專門網站優先 |
| "美國軟體工程師" | LinkedIn, Indeed, ZipRecruiter, Glassdoor | Seek, Naukri, Bayt, BDJobs | 美國市場 + 高薪科技職位 |
| "印度資料科學家" | Naukri, Indeed, LinkedIn | Seek, ZipRecruiter, Bayt, BDJobs, Glassdoor | 印度本地網站 + 國際平台 |
| "杜拜金融工作" | Bayt, LinkedIn, Indeed | Seek, ZipRecruiter, Naukri, BDJobs, Glassdoor | 中東地區專門網站 |

## 💡 完整使用範例 - 跟著做一遍

### 🎯 **範例：搜尋歐洲 AI 工程師職位**

#### 步驟 1：執行搜尋
```bash
# 在命令列執行
python smart_job_search.py "我想找歐洲地區的 AI 工程師工作" --results 50 --output 歐洲AI工程師.csv
```

#### 步驟 2：查看即時輸出
```
🔍 正在分析查詢: "我想找歐洲地區的 AI 工程師工作"
🎯 識別地理區域: Europe (信心度: 1.00)
🏭 識別行業類型: Technology (信心度: 1.00)
🤖 選擇代理: LinkedIn, Indeed, Glassdoor, Google Jobs

📱 開始搜尋...
├─ LinkedIn: ✅ 找到 18 個職位
├─ Indeed: ✅ 找到 15 個職位  
├─ Glassdoor: ✅ 找到 8 個職位
└─ Google Jobs: ✅ 找到 5 個職位

✅ 搜尋完成！總共找到 46 個職位
💾 結果已儲存到: 歐洲AI工程師.csv
📊 詳細報告: 搜尋報告_20240902_033230.txt
```

#### 步驟 3：分析搜尋結果
```python
import pandas as pd

# 讀取結果
jobs = pd.read_csv("歐洲AI工程師.csv")

# 快速分析
print(f"📊 找到 {len(jobs)} 個 AI 工程師職位")
print(f"🏢 涉及 {jobs['company'].nunique()} 家公司")
print(f"🌍 分布在 {jobs['location'].nunique()} 個城市")

# 薪資分析
salary_jobs = jobs[jobs['salary_min'].notna()]
if len(salary_jobs) > 0:
    print(f"💰 平均最低薪資: {salary_jobs['salary_min'].mean():.0f}")
    print(f"💰 平均最高薪資: {salary_jobs['salary_max'].mean():.0f}")

# 熱門城市
print("\n🏙️ 熱門城市:")
print(jobs['location'].value_counts().head())

# 熱門公司
print("\n🏆 熱門公司:")
print(jobs['company'].value_counts().head())
```

#### 步驟 4：查看代理報告
```python
# 讀取詳細報告
with open("搜尋報告_20240902_033230.txt", "r", encoding="utf-8") as f:
    report = f.read()
    print(report)
```

### 多平台搜尋

```python
from jobseeker import scrape_jobs

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

## 🌐 全球求職網站支援

### 🗺️ **按地區分類的支援平台**

#### 🇪🇺 **歐洲地區**
| 平台 | 網站 | 特色 | 支援國家 |
|------|------|------|----------|
| 🔵 LinkedIn | linkedin.com | 專業人脈、高階職位 | 全歐洲 |
| 🟢 Indeed | indeed.com | 職位數量最多 | 英國、德國、法國、荷蘭等 |
| 🟠 Glassdoor | glassdoor.com | 公司評價、薪資透明 | 英國、德國、法國等 |
| 🔴 Google Jobs | google.com/jobs | 整合多平台職位 | 全歐洲 |

#### 🇺🇸 **北美地區**
| 平台 | 網站 | 特色 | 支援國家 |
|------|------|------|----------|
| 🔵 LinkedIn | linkedin.com | 專業網絡、科技職位 | 美國、加拿大 |
| 🟢 Indeed | indeed.com | 最大職位搜尋引擎 | 美國、加拿大 |
| 🟡 ZipRecruiter | ziprecruiter.com | 快速申請、AI 匹配 | 美國 |
| 🟠 Glassdoor | glassdoor.com | 薪資資訊、公司文化 | 美國、加拿大 |

#### 🇦🇺 **澳洲/紐西蘭**
| 平台 | 網站 | 特色 | 支援國家 |
|------|------|------|----------|
| 🟣 Seek | seek.com.au | 澳洲最大求職網站 | 澳洲、紐西蘭 |
| 🔵 LinkedIn | linkedin.com | 專業職位、跨國公司 | 澳洲、紐西蘭 |
| 🟢 Indeed | indeed.com | 國際職位、本地機會 | 澳洲、紐西蘭 |

#### 🇮🇳 **亞洲地區**
| 平台 | 網站 | 特色 | 支援國家 |
|------|------|------|----------|
| 🟤 Naukri | naukri.com | 印度最大求職網站 | 印度 |
| 🟦 BDJobs | bdjobs.com | 孟加拉本地職位 | 孟加拉 |
| 🔵 LinkedIn | linkedin.com | 跨國企業、科技職位 | 全亞洲 |
| 🟢 Indeed | indeed.com | 國際職位機會 | 印度、新加坡等 |

#### 🕌 **中東地區**
| 平台 | 網站 | 特色 | 支援國家 |
|------|------|------|----------|
| 🟫 Bayt | bayt.com | 中東最大求職網站 | 阿聯酋、沙烏地、科威特等 |
| 🔵 LinkedIn | linkedin.com | 跨國企業職位 | 全中東 |
| 🟢 Indeed | indeed.com | 國際職位機會 | 阿聯酋、沙烏地等 |

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
from jobseeker import scrape_jobs

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

1. 在 `jobseeker/` 目錄下創建新的平台目錄
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

## ⚠️ 重要注意事項

### 🔒 **合法使用**
- ✅ **遵守網站條款**：請確保您的使用符合各求職網站的服務條款
- ✅ **個人使用**：建議僅用於個人求職、學術研究或小規模數據分析
- ❌ **商業濫用**：請勿用於大規模商業爬蟲或違反網站政策的行為

### 🚦 **使用建議**
- ⏰ **合理頻率**：避免過於頻繁的請求，建議每次搜尋間隔 30 秒以上
- 📊 **適量搜尋**：單次搜尋建議不超過 100 個職位
- 🔄 **定期更新**：職位資訊會隨時變化，建議定期重新搜尋

### 📋 **資料品質**
- 🎯 **準確性**：爬取的資料可能因網站結構變更而受影響
- 🔗 **連結有效性**：職位連結可能會過期，建議及時查看
- 💰 **薪資資訊**：部分職位可能沒有公開薪資資訊

### ⚖️ **法律責任**
使用者需自行承擔使用本工具的法律責任，開發者不對任何使用後果負責。

## 🚀 未來發展：遷移計劃詳解

### 📁 **完整遷移計劃文檔**

我們正在進行一項重大的架構遷移，從服務器依賴轉向客戶端解決方案。這個轉變將為用戶帶來更好的性能、隱私保護和成本效益。

#### 📋 **遷移計劃概覽**

**查看完整文檔**: 📂 [`migration_plans/`](./migration_plans/) 文件夾包含詳細的技術文檔和實施指南

##### 🏗️ **[01_客戶端解決方案](./migration_plans/01_client_side_solutions/)**
- **桌面應用程式**: Electron + Python 整合，完整離線功能
- **瀏覽器擴充功能**: Chrome/Firefox 外掛，直接在求職網站增強功能  
- **漸進式網頁應用**: PWA 手機版，支援離線搜尋和通知
- **性能比較分析**: 各種方案的詳細技術評估

##### 💰 **[02_商業模式](./migration_plans/02_business_models/)**
- **免費增值策略**: 基本功能免費，進階功能付費
- **訂閱服務**: 即時薪資分析、公司評價、市場趨勢
- **企業解決方案**: 團隊管理、批量授權、自定義品牌
- **收益預測**: 3年財務規劃和成長策略

##### 🔧 **[03_實施指南](./migration_plans/03_implementation_guides/)**
- **桌面應用設置**: 完整的 Electron 開發指南
- **授權服務器**: 身份驗證和驗證系統
- **高級數據 API**: 訂閱服務的後端架構
- **支付整合**: Stripe 和訂閱管理系統

##### 🌐 **[04_部署策略](./migration_plans/04_deployment_strategies/)**
- **建構與打包**: 應用程式分發方法
- **雲端基礎設施**: 授權服務器部署方案
- **CI/CD 流水線**: 自動化部署工作流程
- **監控與分析**: 業務指標追蹤系統

##### 🏛️ **[05_技術架構](./migration_plans/05_technical_architecture/)**
- **架構圖表**: 系統概覽和數據流程
- **數據庫架構**: 授權管理和用戶數據
- **API 文檔**: 高級服務規格說明
- **安全措施**: 防盜版和數據保護

### 🎯 **為什麼要遷移？**

#### 🚫 **當前服務器限制**
- **性能問題**: 冷啟動延遲 5-15 秒
- **成本負擔**: 每月服務器費用 $5-20
- **資源限制**: 有限的服務器 CPU/RAM
- **可擴展性**: 服務器依賴瓶頸

#### ✅ **客戶端解決方案優勢**
- **卓越性能**: 即時響應，充分利用本地資源
- **零運營成本**: 核心功能無需服務器費用
- **可持續盈利**: 增值服務和高級功能
- **自然擴展**: 用戶硬件自然擴展處理能力

### 📅 **開發時程表**

#### 🏃‍♂️ **第一階段：核心遷移 (1-2個月)**
1. **桌面應用開發**
   - 基本 Electron 應用與 JobSpy 整合
   - 本地 Python 執行環境
   - 簡潔的求職搜尋 UI

2. **授權系統設置**
   - 基本授權驗證服務器
   - 硬體指紋識別
   - 免費 vs 專業版區分

#### 💎 **第二階段：商業模式 (3-4個月)**
1. **高級服務後端**
   - 薪資智能 API
   - 公司洞察服務
   - 市場趨勢分析

2. **支付整合**
   - Stripe 訂閱管理
   - 授權密鑰生成
   - 客戶帳戶門戶

#### 🏢 **第三階段：規模化與企業版 (5-6個月)**
1. **企業功能**
   - 團隊管理儀表板
   - 批量授權系統
   - 自定義品牌選項

2. **替代平台**
   - 瀏覽器擴充功能版本
   - 移動 PWA 應用
   - 第三方整合 API

### 🤝 **如何參與我們的遷移計劃**

#### 💡 **用戶參與方式**

##### 📝 **需求反饋**
- **功能建議**: 告訴我們您最需要的功能
- **用戶體驗**: 分享您的使用習慣和偏好
- **定價意見**: 幫助我們制定合理的定價策略

##### 🧪 **Beta 測試**
- **早期體驗**: 第一時間試用新功能
- **錯誤報告**: 幫助我們發現和修復問題
- **性能測試**: 在不同設備上測試性能表現

##### 🌟 **社群推廣**
- **分享經驗**: 在社交媒體分享使用心得
- **推薦朋友**: 幫助更多人發現 JobSpy
- **內容創作**: 製作教學影片或部落格文章

#### 👨‍💻 **開發者貢獻**

##### 🔧 **技術貢獻**
- **代碼提交**: 參與核心功能開發
- **功能模組**: 開發新的求職網站支援
- **性能優化**: 改進搜尋算法和數據處理

##### 📚 **文檔改進**
- **技術文檔**: 完善 API 和架構文檔
- **用戶指南**: 撰寫使用教程和最佳實踐
- **多語言支援**: 翻譯文檔到不同語言

##### 🏗️ **基礎設施**
- **CI/CD 優化**: 改進自動化部署流程
- **測試覆蓋**: 增加單元測試和整合測試
- **監控系統**: 建立性能和錯誤監控

#### 💰 **資金支持**

##### 🎁 **贊助方式**
- **GitHub Sponsors**: 月度或一次性贊助
- **Buy Me a Coffee**: 小額打賞支持
- **企業贊助**: 企業級長期合作

##### 🏆 **贊助者權益**
- **優先支援**: 專用技術支援通道
- **早期訪問**: 新功能搶先體驗
- **定制服務**: 個性化功能開發
- **品牌曝光**: 在項目中展示贊助商標

### 📞 **聯繫我們**

#### 📧 **溝通渠道**
- **GitHub Discussions**: 技術討論和功能建議
- **Discord 社群**: 即時聊天和社群互動 
- **Email**: 商業合作和私人諮詢
- **定期會議**: 月度社群線上會議

#### 📋 **參與步驟**
1. **加入社群**: 關注我們的 GitHub 和 Discord
2. **閱讀文檔**: 深入了解遷移計劃細節
3. **選擇貢獻方式**: 根據您的技能和興趣選擇參與方式
4. **開始行動**: 提交第一個 Issue 或 Pull Request

> **🌟 重要提醒**: 這是一個開源社群項目，我們歡迎任何形式的貢獻！無論您是技術專家還是普通用戶，都可以在這個項目中找到屬於自己的貢獻方式。讓我們一起打造下一代最優秀的求職工具！

## ❓ 常見問題 FAQ

### Q: 為什麼建議使用本地部署而不是雲端部署？
A: **雲端部署會有以下問題**：
- ⏰ **長時間等待**: 冷啟動可能需要 5-15 秒甚至更久
- 🐌 **效能限制**: 伺服器資源有限，處理速度較慢
- 💸 **成本問題**: 每月都有伺服器費用
- 🔌 **網路依賴**: 需要穩定的網路連線

**本地部署優勢**: 即時響應、無成本、完整效能、隱私保護

### Q: 何時可以使用新的桌面應用或瀏覽器擴充功能？
A: 我們預計：
- **桌面應用 Beta 版**: 2-3 個月內發布
- **瀏覽器擴充功能**: 5-6 個月內發布
- **移動 PWA 應用**: 6-8 個月內發布

請關注我們的 [GitHub](https://github.com/jason660519/jobseeker) 獲取最新進度，或 [參與測試](#-參與我們的遷移計劃) 幫助加速開發！

### Q: 為什麼某些求職網站沒有被使用？
A: JobSpy 的智能路由系統會根據您的查詢自動選擇最適合的求職網站。例如，搜尋歐洲職位時不會使用 Seek（澳洲專用）或 Naukri（印度專用）。

### Q: 搜尋結果為什麼比預期少？
A: 可能的原因：
- 查詢條件太具體
- 該地區/行業職位較少
- 部分網站暫時無法訪問
- 建議放寬搜尋條件或嘗試不同的關鍵字

### Q: 職位連結無法開啟怎麼辦？
A: 職位連結可能會過期，這是正常現象。建議：
- 及時查看搜尋結果
- 使用 `job_url_direct` 欄位的直接申請連結
- 直接到公司官網搜尋相同職位

### Q: 如何提高搜尋準確度？
A: 建議：
- 使用具體的職位名稱（如「資料科學家」而非「數據工作」）
- 明確指定地理位置（如「倫敦」而非「歐洲」）
- 使用英文關鍵字搜尋國際職位

## 🤝 貢獻與支援

### 💡 **如何貢獻**
歡迎提交 Issue 和 Pull Request！

1. 🍴 Fork 本專案
2. 🌿 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 💾 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 📤 推送到分支 (`git push origin feature/amazing-feature`)
5. 🔄 開啟 Pull Request

### 🐛 **回報問題**
如果您遇到問題，請在 [GitHub Issues](https://github.com/jason660519/jobseeker/issues) 提交，並包含：
- 您的查詢內容
- 錯誤訊息
- 作業系統和 Python 版本

### 📧 **聯絡我們**
- GitHub: [jason660519/jobseeker](https://github.com/jason660519/jobseeker)
- Issues: [提交問題](https://github.com/jason660519/jobseeker/issues)

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

感謝所有為開源社群貢獻的開發者們！特別感謝：
- 所有提交 Issue 和 PR 的貢獻者
- 測試和回饋的使用者
- 開源 Python 生態系統

---

## 🎯 開始您的求職之旅

```bash
# 立即開始搜尋！
python smart_job_search.py "您想要的工作"
```

**💼 祝您求職順利！找到理想工作！**

---

**⚠️ 免責聲明**：本工具僅供學習、研究和個人求職使用。使用者需自行確保符合相關網站的使用條款和當地法律法規。開發者不對使用本工具產生的任何後果承擔責任。
