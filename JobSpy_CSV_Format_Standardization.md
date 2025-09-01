# JobSpy CSV 格式統一標準化說明

## 概述

JobSpy 是一個多平台職位爬蟲工具，能夠從 Indeed、LinkedIn、ZipRecruiter、Glassdoor 等多個求職網站抓取職位資料。儘管各網站的原始資料格式差異很大，JobSpy 通過統一的格式標準化機制，確保最終輸出的 CSV 檔案格式完全一致。

## 標準 CSV 格式規範

### 核心欄位 (14個)

| 欄位名稱 | 資料類型 | 說明 | 範例 |
|---------|---------|------|------|
| `id` | string | 職位唯一識別碼，包含網站前綴 | `in-abc123`, `li-def456` |
| `site` | string | 來源網站名稱 | `indeed`, `linkedin` |
| `job_url` | string | 職位詳細頁面連結 | `https://www.indeed.com/viewjob?jk=...` |
| `title` | string | 職位標題 | `Software Engineer` |
| `company` | string | 公司名稱 | `Google Inc.` |
| `location` | string | 工作地點，格式: "City, State" | `San Francisco, CA` |
| `date_posted` | string | 發布日期，ISO格式 | `2024-01-15` |
| `job_type` | string | 職位類型 | `fulltime`, `parttime`, `contract` |
| `salary_source` | string | 薪資來源 | `direct`, `glassdoor`, `estimated` |
| `interval` | string | 薪資週期 | `yearly`, `monthly`, `hourly` |
| `min_amount` | float | 最低薪資 | `80000.0` |
| `max_amount` | float | 最高薪資 | `120000.0` |
| `currency` | string | 貨幣代碼 | `USD`, `EUR` |
| `is_remote` | boolean | 是否遠端工作 | `True`, `False` |

### 擴展欄位 (20個)

包括 `description`、`company_url`、`company_addresses`、`company_industry`、`company_num_employees`、`company_revenue`、`company_description`、`logo_photo_url`、`banner_photo_url`、`ceo_name`、`ceo_photo_url`、`emails`、`skills`、`experience_range`、`degree_required`、`benefits`、`company_type`、`company_size`、`company_founded`、`company_rating` 等。

## 格式統一機制

### 1. 原始資料差異

不同網站的原始資料格式存在顯著差異：

**Indeed 原始格式:**
```json
{
  "title": "Software Engineer",
  "company": "AMERICAN SYSTEMS",
  "location": {"city": "Arlington", "state": "VA"},
  "salary": "$150,000 - $200,000 per year",
  "posted_date": "1 day ago",
  "employment_type": "Full-time"
}
```

**LinkedIn 原始格式:**
```json
{
  "job_title": "Software Engineer - Early Career",
  "company_name": "Lockheed Martin",
  "job_location": "Sunnyvale, CA",
  "compensation": {"amount": 120000, "currency": "USD", "period": "yearly"},
  "post_date": "2024-01-15",
  "work_type": "fulltime"
}
```

**ZipRecruiter 原始格式:**
```json
{
  "position": "Software Engineer - New Grad",
  "employer": "ZipRecruiter",
  "city_state": "Santa Monica, CA",
  "pay_range": "$130,000 - $150,000 annually",
  "date_posted": "2024-01-14",
  "job_category": "full-time"
}
```

### 2. 統一轉換邏輯

#### 職位 ID 標準化
- Indeed: `in-` + 原始ID
- LinkedIn: `li-` + 原始ID  
- ZipRecruiter: `zr-` + 原始ID

#### 薪資資料標準化
- 解析各種薪資文字格式
- 統一轉換為 `min_amount`、`max_amount`、`interval`、`currency` 四個欄位
- 支援年薪、月薪、時薪的自動識別和轉換

#### 日期格式標準化
- 相對時間 ("1 day ago") → ISO日期格式 ("2024-01-15")
- 各種日期格式 → 統一的 YYYY-MM-DD 格式

#### 地點資訊標準化
- 結構化物件 `{city, state}` → 統一字串 "City, State"
- 處理國際地點格式差異

#### 職位類型標準化
- 各種表示方式 → 標準值: `fulltime`、`parttime`、`contract`、`temporary`

### 3. 技術實現

#### JobPost 模型
```python
class JobPost(BaseModel):
    id: Optional[str] = None
    site: Optional[Site] = None
    job_url: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[Location] = None
    # ... 其他欄位
```

#### 轉換流程
1. 各網站爬蟲抓取原始資料
2. 轉換為統一的 `JobPost` 模型
3. 批次轉換為 Pandas DataFrame
4. 按照 `desired_order` 排序欄位
5. 輸出標準化 CSV 檔案

#### 欄位順序控制
```python
desired_order = [
    "id", "site", "job_url", "title", "company", "location",
    "date_posted", "job_type", "salary_source", "interval",
    "min_amount", "max_amount", "currency", "is_remote",
    "description", "company_url", "company_addresses",
    # ... 其他欄位
]
```

## 使用範例

### 基本使用
```python
from jobspy import scrape_jobs
import pandas as pd

# 多平台搜尋
jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "ziprecruiter"],
    search_term="software engineer",
    location="San Francisco, CA",
    results_wanted=50
)

# 輸出統一格式 CSV
jobs.to_csv("unified_jobs.csv", index=False)
```

### 格式驗證
```python
# 檢查欄位完整性
expected_columns = 34
actual_columns = len(jobs.columns)
print(f"欄位數量: {actual_columns}/{expected_columns}")

# 檢查必要欄位
required_fields = ["id", "site", "title", "company", "location"]
missing_fields = [field for field in required_fields if field not in jobs.columns]
if not missing_fields:
    print("✅ 所有必要欄位都存在")
```

## 優勢與特點

### 1. 完全統一
- 不論來源網站，輸出格式完全一致
- 固定的 34 個欄位，固定的欄位順序
- 統一的資料類型和格式規範

### 2. 資料完整性
- 自動填充缺失欄位為 `None`
- 保留所有可用資訊
- 支援網站特有欄位的標準化處理

### 3. 易於分析
- 標準化格式便於 Pandas 分析
- 支援多網站資料合併
- 一致的欄位名稱和資料類型

### 4. 擴展性
- 新增網站時只需實現對應的轉換邏輯
- 標準格式保持不變
- 向後相容性良好

## 總結

JobSpy 的 CSV 格式統一機制是其核心優勢之一。通過統一的 `JobPost` 模型、標準化的轉換邏輯和固定的輸出格式，JobSpy 成功解決了多平台職位資料格式不一致的問題，為使用者提供了一致、可靠的資料輸出，大大簡化了後續的資料分析和處理工作。

無論原始資料來自哪個網站，最終的 CSV 檔案都遵循相同的 34 欄位標準格式，確保了資料的一致性和可用性。