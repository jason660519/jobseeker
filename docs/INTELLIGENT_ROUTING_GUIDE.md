# jobseeker 智能路由系統使用指南

## 概述

jobseeker 智能路由系統是一個革命性的功能，能夠根據用戶的查詢自動選擇最適合的爬蟲代理（agents），從而提高搜索效率並減少不必要的失敗。

## 🚀 主要特性

### 1. 智能代理選擇
- **地理位置檢測**: 自動識別查詢中的國家、州省、城市信息
- **行業分類識別**: 根據關鍵詞判斷目標行業
- **距離範圍分析**: 解析搜索半徑和本地化需求
- **語言檢測**: 支持中文、英文、阿拉伯語等多語言

### 2. 支持的代理

| 代理 | 專長地區 | 強項 | 可靠性 |
|------|----------|------|--------|
| **Seek** | 澳洲、紐西蘭 | 建築、技工、政府職位 | 90% |
| **Indeed** | 全球 | 大量職位、各級別 | 85% |
| **LinkedIn** | 全球 | 專業職位、高級職位、科技 | 88% |
| **Glassdoor** | 美國、加拿大、歐洲 | 薪資信息、公司評價 | 82% |
| **ZipRecruiter** | 美國、加拿大 | 快速申請、本地職位 | 80% |
| **Naukri** | 印度 | 科技、新鮮人職位 | 87% |
| **Bayt** | 中東、北非 | 阿拉伯語、石油天然氣、金融 | 83% |
| **BDJobs** | 孟加拉 | 本地職位、入門級 | 78% |
| **Google Jobs** | 全球 | 聚合搜索、發現新職位 | 75% |

## 📖 使用方法

### 1. 基本使用

```python
from jobseeker.route_manager import smart_scrape_jobs

# 簡單搜索
result = smart_scrape_jobs(
    user_query="請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作",
    results_wanted=15
)

print(f"找到 {result.total_jobs} 個職位")
print(f"使用的代理: {[a.value for a in result.successful_agents]}")
```

### 2. 高級使用

```python
from jobseeker.route_manager import RouteManager

# 創建路由管理器
manager = RouteManager(max_workers=3)

# 執行智能搜索
result = manager.smart_scrape_jobs(
    user_query="Looking for senior software engineer jobs in San Francisco",
    location="San Francisco, CA",
    results_wanted=20,
    hours_old=72,  # 最近3天
    country_indeed="US"
)

# 查看詳細結果
for exec_result in result.execution_results:
    print(f"{exec_result.agent.value}: {exec_result.job_count} 職位")
```

### 3. 命令行使用

```bash
# 基本搜索
python smart_job_search.py "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"

# 帶參數搜索
python smart_job_search.py "Looking for software engineer jobs in San Francisco" --results 20 --hours 48

# 保存結果
python smart_job_search.py "Find marketing jobs in Mumbai" --output results.csv

# 只顯示路由決策
python smart_job_search.py "尋找台北的資料科學家工作" --dry-run --explain
```

## 🎯 智能路由示例

### 示例 1: 澳洲建築業

**查詢**: "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"

**路由決策**:
- **選中代理**: Seek (主要), Indeed, LinkedIn (次要)
- **理由**: 地理位置匹配澳洲 + 建築行業 + 本地搜索
- **信心度**: 0.85

### 示例 2: 美國科技業

**查詢**: "Looking for senior software engineer jobs in San Francisco Bay Area"

**路由決策**:
- **選中代理**: LinkedIn (主要), Indeed, ZipRecruiter, Glassdoor
- **理由**: 地理位置匹配美國 + 科技行業 + 高級職位
- **信心度**: 0.92

### 示例 3: 印度科技業

**查詢**: "Find data scientist jobs in Bangalore, India for fresher candidates"

**路由決策**:
- **選中代理**: Naukri (主要), Indeed, LinkedIn
- **理由**: 地理位置匹配印度 + 科技行業 + 新鮮人職位
- **信心度**: 0.88

### 示例 4: 中東金融業

**查詢**: "Looking for investment banking analyst positions in Dubai, UAE"

**路由決策**:
- **選中代理**: Bayt (主要), LinkedIn, Indeed
- **理由**: 地理位置匹配中東 + 金融行業
- **信心度**: 0.83

## ⚙️ 配置選項

### 1. 自定義配置文件

創建 `config/intelligent_routing_config.json` 文件來自定義路由行為：

```json
{
  "routing_settings": {
    "max_concurrent_agents": 4,
    "confidence_threshold": 0.6,
    "fallback_enabled": true
  },
  "geographic_regions": {
    "custom_regions": [
      {
        "name": "Taiwan",
        "countries": ["taiwan", "台灣"],
        "primary_agents": ["indeed", "linkedin"]
      }
    ]
  }
}
```

### 2. 代理優先級調整

```python
from jobseeker.route_manager import RouteManager

# 使用自定義配置
manager = RouteManager(config_path="config/intelligent_routing_config.json")
```

## 🔍 路由決策分析

### 1. 僅分析路由（不執行搜索）

```python
from jobseeker.intelligent_router import IntelligentRouter

router = IntelligentRouter()
decision = router.analyze_query("你的查詢")

print(f"選中代理: {[a.value for a in decision.selected_agents]}")
print(f"信心度: {decision.confidence_score}")
print(f"決策理由: {decision.reasoning}")
```

### 2. 詳細解釋

```python
explanation = router.get_routing_explanation(decision)
print(explanation)
```

## 📊 性能監控

### 1. 執行統計

```python
manager = RouteManager()

# 執行多次搜索後
stats = manager.get_routing_statistics()
print(f"總執行次數: {stats['total_executions']}")
print(f"代理成功率: {stats['agent_success_rate']}")
```

### 2. 執行歷史

```python
history = manager.get_execution_history()
for entry in history:
    print(f"查詢: {entry['query']}")
    print(f"結果: {entry['result'].total_jobs} 職位")
```

## 🛠️ 高級功能

### 1. 自定義規則

在配置文件中添加自定義路由規則：

```json
{
  "custom_rules": [
    {
      "name": "prefer_local_for_trades",
      "condition": {
        "keywords": ["electrician", "plumber", "carpenter"],
        "has_location": true
      },
      "action": {
        "boost_local_agents": 0.2
      }
    }
  ]
}
```

### 2. 並發控制

```python
# 限制並發代理數量
manager = RouteManager(max_workers=2)

# 設置超時時間
result = manager.smart_scrape_jobs(
    user_query="your query",
    timeout=120  # 2分鐘超時
)
```

### 3. 錯誤處理

```python
try:
    result = smart_scrape_jobs(user_query="your query")
    
    if result.failed_agents:
        print(f"失敗的代理: {[a.value for a in result.failed_agents]}")
        print("系統已自動使用後備代理")
        
except Exception as e:
    print(f"搜索失敗: {e}")
```

## 🌍 多語言支持

智能路由系統支持多種語言的查詢：

```python
# 中文查詢
result = smart_scrape_jobs("請幫我找香港的會計師工作")

# 英文查詢
result = smart_scrape_jobs("Find marketing jobs in Paris, France")

# 混合語言查詢
result = smart_scrape_jobs("尋找新加坡的 software engineer 職位")
```

## 📈 最佳實踐

### 1. 查詢優化

**好的查詢示例**:
- ✅ "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"
- ✅ "Looking for senior software engineer jobs in San Francisco Bay Area"
- ✅ "Find data scientist positions in Mumbai, India within 25km"

**避免的查詢**:
- ❌ "找工作" (太模糊)
- ❌ "jobs" (缺乏具體信息)
- ❌ "高薪工作" (沒有地理或行業信息)

### 2. 參數設置

```python
# 推薦設置
result = smart_scrape_jobs(
    user_query="具體的查詢",
    results_wanted=15,  # 適中的數量
    hours_old=72,       # 最近3天
    country_indeed="specific_country"  # 具體國家
)
```

### 3. 結果處理

```python
if result.combined_jobs_data is not None:
    # 去重處理
    unique_jobs = result.combined_jobs_data.drop_duplicates(
        subset=['title', 'company'], keep='first'
    )
    
    # 保存結果
    unique_jobs.to_csv('jobs.csv', index=False)
```

## 🔧 故障排除

### 常見問題

1. **沒有找到任何職位**
   - 檢查查詢是否過於具體
   - 嘗試擴大搜索範圍
   - 使用更通用的關鍵詞

2. **某些代理總是失敗**
   - 檢查網路連接
   - 查看代理的地理限制
   - 考慮使用代理伺服器

3. **路由決策不準確**
   - 提供更具體的地理信息
   - 使用行業相關關鍵詞
   - 考慮自定義配置

### 調試模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 啟用詳細日誌
result = smart_scrape_jobs(
    user_query="your query",
    verbose=True
)
```

## 📞 支援與貢獻

- **問題回報**: 請在 GitHub Issues 中提交
- **功能建議**: 歡迎提交 Pull Request
- **文檔改進**: 幫助我們完善文檔

## 📄 授權

本項目採用 MIT 授權條款。詳見 LICENSE 文件。

---

**jobseeker 智能路由系統** - 讓工作搜索更智能、更高效！
