# 🔍 JobSpy - 智能職位搜尋工具

> **一個強大且易用的 Python 職位搜尋工具，讓找工作變得更簡單！**

無論您是求職者、HR、還是數據分析師，JobSpy 都能幫您快速從全球主流求職網站搜集職位資訊。只需一行指令，就能搜尋數百個職位！

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
from jobspy.route_manager import smart_scrape_jobs

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

當您執行搜尋後，JobSpy 會產生以下檔案：

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

JobSpy 的智能路由系統會為每次搜尋產生詳細的代理使用報告，幫您了解：
- 🎯 **哪些求職網站被選中**（啟用的代理）
- ❌ **哪些求職網站未被使用**（未啟用的代理）
- 📊 **每個網站的搜尋效果**
- 🧠 **系統的決策邏輯**

### 📊 **代理報告範例解讀**

```
=== JobSpy 智能路由報告 ===
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

## ❓ 常見問題 FAQ

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