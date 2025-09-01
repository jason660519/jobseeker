# JobSpy 原始資料 vs 統一格式對比報告

## 📁 檔案存放位置

### 🗂️ 原始資料檔案位置
```
tests_collection/test_results/[測試類型]/[測試時間]/
├── indeed_[job_type]_raw_data.json     # Indeed原始JSON資料
├── linkedin_[job_type]_raw_data.json   # LinkedIn原始JSON資料
├── glassdoor_[job_type]_raw_data.json  # Glassdoor原始JSON資料
├── naukri_[job_type]_raw_data.json     # Naukri原始JSON資料
└── seek_[job_type]_raw_data.json       # Seek原始JSON資料
```

### 📊 統一格式CSV檔案位置
```
tests_collection/test_results/[測試類型]/[測試時間]/
├── indeed_[job_type]_jobs.csv          # Indeed統一格式CSV
├── linkedin_[job_type]_jobs.csv        # LinkedIn統一格式CSV
├── glassdoor_[job_type]_jobs.csv       # Glassdoor統一格式CSV
├── naukri_[job_type]_jobs.csv          # Naukri統一格式CSV
├── seek_[job_type]_jobs.csv            # Seek統一格式CSV
└── all_sites_[job_type]_combined.csv   # 所有網站合併CSV
```

### 🔍 範例測試目錄
- `tests_collection\test_results\ml_engineer_tests\ml_engineer_test_fixed_20250901_212155`
- `tests_collection\test_results\enhanced_scraper_tests\enhanced_test_20250901_215209`
- `tests_collection\test_results\ui_ux_tests\ui_ux_test_20250901_213456`

## 🌐 各網站原始資料格式對比

### 1. Indeed 原始資料特點
```json
{
  "id": "in-b31e6c0e88552ce5",
  "site": "indeed",
  "job_url": "https://au.indeed.com/viewjob?jk=b31e6c0e88552ce5",
  "job_url_direct": "https://jobs.deloitte.com.au/job/...",
  "title": "Senior Full Stack Engineer",
  "company": "Deloitte",
  "location": "Melbourne, VIC, AU",
  "date_posted": "2025-09-01",
  "description": "完整的職位描述內容...",
  "company_industry": NaN,
  "company_url": "https://au.indeed.com/cmp/Deloitte",
  "company_logo": "https://d2q79iu7y748jz.cloudfront.net/...",
  "company_num_employees": "10,000+",
  "company_revenue": "more than $10B (USD)"
}
```

**特點：**
- ✅ 包含詳細的職位描述
- ✅ 豐富的公司資訊（員工數、營收等）
- ✅ 公司Logo和直接連結
- ❌ 薪資資訊通常為空

### 2. LinkedIn 原始資料特點
```json
{
  "id": "li-4292864287",
  "site": "linkedin",
  "job_url": "https://www.linkedin.com/jobs/view/4292864287",
  "job_url_direct": null,
  "title": "Machine Learning Data Engineer",
  "company": "IntelligenceBank",
  "location": "Southbank, Victoria, Australia",
  "date_posted": "2025-08-29",
  "description": null,
  "company_url": "https://au.linkedin.com/company/intelligencebank",
  "job_level": ""
}
```

**特點：**
- ✅ 職位基本資訊完整
- ✅ 公司LinkedIn頁面連結
- ❌ 職位描述經常為空
- ❌ 公司詳細資訊較少
- ❌ 薪資資訊通常缺失

### 3. Glassdoor 原始資料特點
```json
{
  "id": "gd-1009861036036",
  "site": "glassdoor",
  "job_url": "https://www.glassdoor.com.au/job-listing/j?jl=1009861036036",
  "title": "Security Architect",
  "company": "Chandler Macleod",
  "location": "Docklands",
  "salary_source": "direct_data",
  "interval": "yearly",
  "min_amount": 150000.0,
  "max_amount": 200000.0,
  "currency": "AUD",
  "listing_type": "sponsored",
  "description": "詳細的職位描述..."
}
```

**特點：**
- ✅ 薪資資訊最完整（範圍、幣別、週期）
- ✅ 詳細的職位描述
- ✅ 標示廣告類型（sponsored/organic）
- ✅ 公司Logo連結
- ❌ 公司詳細資訊相對較少

## 📊 統一格式CSV特點

### 標準34欄位結構
```csv
id,site,job_url,title,company,location,date_posted,job_type,salary_source,
interval,min_amount,max_amount,currency,is_remote,job_level,job_function,
listing_type,emails,description,company_industry,company_url,company_logo,
company_url_direct,company_addresses,company_num_employees,company_revenue,
company_description,city,state,country,zip_code,benefits,
company_description_from_job,company_size,search_date
```

### 統一格式範例
```csv
id,site,job_url,title,company,location,date_posted
seek_539b40b35eff,seek,https://www.seek.com.au/job/86830243,"ML Solutions Engineer","Tech & Data People","Melbourne, VIC, Australia",2025-09-01
li-4292864287,linkedin,https://www.linkedin.com/jobs/view/4292864287,"Machine Learning Data Engineer","IntelligenceBank","Southbank, Victoria, Australia",2025-08-29
gd-1009861036036,glassdoor,https://www.glassdoor.com.au/job-listing/j?jl=1009861036036,"Security Architect","Chandler Macleod","Docklands",2025-09-01
```

## 🔄 格式轉換過程

### 轉換流程
```
原始JSON資料 → JobPost模型 → 統一CSV格式
     ↓              ↓            ↓
各網站特有格式   標準化處理    34欄位統一格式
```

### 關鍵轉換邏輯

1. **職位ID標準化**
   - Indeed: `in-` 前綴
   - LinkedIn: `li-` 前綴
   - Glassdoor: `gd-` 前綴
   - Seek: `seek_` 前綴

2. **薪資資訊統一**
   - 統一為 `min_amount`, `max_amount`, `currency`, `interval` 格式
   - 處理不同網站的薪資表示方式

3. **日期格式標準化**
   - 統一為 `YYYY-MM-DD` 格式
   - 處理相對日期（如"2 days ago"）

4. **地點資訊標準化**
   - 統一地點格式
   - 提取城市、州/省、國家資訊

5. **缺失欄位處理**
   - 自動填充為 `None` 或空值
   - 確保所有CSV都有相同的34個欄位

## 📈 統計對比

| 網站 | 原始資料筆數 | 統一CSV筆數 | 主要優勢 | 主要限制 |
|------|-------------|-------------|----------|----------|
| Indeed | 15 | 15 | 詳細描述、公司資訊 | 薪資資訊缺失 |
| LinkedIn | 15 | 15 | 職位基本資訊完整 | 描述經常為空 |
| Glassdoor | 15 | 15 | 薪資資訊最完整 | 公司資訊較少 |
| Seek | 15 | 15 | 澳洲本地化 | 格式較簡單 |
| Naukri | 15 | 15 | 印度市場專業 | 地區限制 |

## 🎯 JobSpy統一格式的優勢

### 1. **完全統一**
- 所有網站輸出相同的34欄位格式
- 固定的欄位順序和命名規範
- 標準化的資料類型

### 2. **資料完整性**
- 自動填充缺失欄位
- 保持資料結構一致性
- 避免因欄位缺失導致的分析問題

### 3. **易於分析**
- 可直接合併不同網站的資料
- 支援跨平台職位比較
- 便於進行資料分析和視覺化

### 4. **擴展性**
- 新增網站時只需實現轉換邏輯
- 不影響現有的資料格式
- 支援未來功能擴展

## 🔍 使用建議

1. **分析原始資料**：當需要網站特有資訊時
2. **使用統一格式**：進行跨平台分析和比較時
3. **合併資料**：使用 `all_sites_[job_type]_combined.csv` 進行整體分析
4. **資料驗證**：定期檢查轉換後的資料完整性

---

*此報告展示了JobSpy如何成功解決多平台職位資料格式不一致的問題，實現了「最終整理好的csv檔格式大家要統一」的目標。*