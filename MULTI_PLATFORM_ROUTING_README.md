# 多平台智能路由系統

## 概述

多平台智能路由系統是一個先進的職位搜尋調度平台，能夠根據地理位置和查詢特徵智能選擇最適合的人力銀行平台進行異步搜尋。系統支援多個主流平台，包括LinkedIn、Indeed、Google Jobs、Seek、1111人力銀行和104人力銀行等。

## 🏗️ 系統架構

### 核心組件

```
┌─────────────────────────────────────────────────────────────┐
│                    多平台智能路由系統                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  整合API服務     │  │  配置管理器      │  │  演示腳本        │ │
│  │ (FastAPI)       │  │ (Config)        │  │ (Demo)          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  多平台調度器    │  │  狀態同步管理器  │  │  數據完整性管理器│ │
│  │ (Scheduler)     │  │ (Sync Manager)  │  │ (Integrity)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  智能路由器      │  │  任務追蹤器      │  │  Redis存儲       │ │
│  │ (Smart Router)  │  │ (Task Tracker)  │  │ (Storage)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 數據流向

```
用戶請求 → API接收 → 地區檢測 → 平台選擇 → 任務分配 → 併發執行 → 狀態同步 → 結果聚合 → 完整性檢查 → 返回結果
```

## 🚀 主要功能

### 1. 地區導向的智能平台選擇

- **美國地區**: LinkedIn + Indeed + Google Jobs
- **台灣地區**: 1111人力銀行 + 104人力銀行
- **澳洲地區**: Seek + LinkedIn
- **全球地區**: LinkedIn + Indeed + Google Jobs

### 2. 任務分配追蹤

- 實時追蹤每個JSON檔案對應的多個平台任務狀態
- 支援任務優先級管理
- 提供詳細的執行進度報告

### 3. 狀態同步機制

- 即時同步各平台爬蟲執行狀態到中央調度器
- 支援事件驅動的狀態更新
- 平台健康狀況監控

### 4. 錯誤處理流程

- 智能重試機制
- 失敗回滾策略
- 異常通知系統
- 平台故障轉移

### 5. 數據完整性檢查

- 多級驗證機制（基礎、標準、嚴格、全面）
- 數據一致性檢查
- 質量評分系統
- 完整性報告生成

## 📁 文件結構

```
JobSpy/
├── multi_platform_scheduler.py      # 多平台調度器
├── platform_sync_manager.py         # 平台狀態同步管理器
├── data_integrity_manager.py         # 數據完整性管理器
├── integrated_multi_platform_api.py  # 整合API服務
├── multi_platform_config.py          # 配置管理器
├── example_multi_platform_usage.py   # 使用示例
├── MULTI_PLATFORM_ROUTING_README.md  # 本文件
└── config/                           # 配置文件目錄
    ├── development.json              # 開發環境配置
    ├── testing.json                  # 測試環境配置
    ├── staging.json                  # 預發布環境配置
    └── production.json               # 生產環境配置
```

## 🛠️ 安裝和配置

### 1. 環境要求

- Python 3.8+
- Redis 6.0+
- FastAPI
- asyncio
- 相關依賴包

### 2. 安裝依賴

```bash
pip install fastapi uvicorn redis aioredis pydantic
```

### 3. 配置Redis

```bash
# 啟動Redis服務器
redis-server

# 或使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 4. 環境變量設置

```bash
# 設置配置級別
export CONFIG_LEVEL=development  # development, testing, staging, production

# 設置Redis連接
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your_password  # 可選

# 設置API端口
export API_PORT=8000
```

## 🚀 快速開始

### 1. 啟動API服務器

```bash
# 方法1: 直接運行
python integrated_multi_platform_api.py

# 方法2: 使用uvicorn
uvicorn integrated_multi_platform_api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 運行演示腳本

```bash
python example_multi_platform_usage.py
```

### 3. API使用示例

#### 提交搜尋任務

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "software engineer",
       "location": "San Francisco, CA",
       "region": "us",
       "max_results": 25,
       "priority": 1,
       "validation_level": "standard"
     }'
```

#### 查詢任務狀態

```bash
curl "http://localhost:8000/jobs/{job_id}/status"
```

#### 獲取系統狀態

```bash
curl "http://localhost:8000/system/status"
```

## 📊 API文檔

### 主要端點

| 端點 | 方法 | 描述 |
|------|------|------|
| `/search` | POST | 提交多平台搜尋任務 |
| `/jobs/{job_id}/status` | GET | 獲取任務狀態 |
| `/jobs/{job_id}/results` | GET | 獲取任務結果 |
| `/jobs/{job_id}/cancel` | POST | 取消任務 |
| `/system/status` | GET | 獲取系統狀態 |
| `/platforms/health` | GET | 獲取平台健康狀態 |
| `/health` | GET | 健康檢查 |
| `/docs` | GET | API文檔 (Swagger UI) |

### 請求模型

#### SearchRequest

```json
{
  "query": "string",           // 搜尋查詢 (必填)
  "location": "string",        // 地點
  "region": "string",          // 地區 (us, taiwan, australia, global)
  "platforms": ["string"],     // 指定平台列表 (可選)
  "max_results": 25,           // 每個平台最大結果數
  "priority": 1,               // 任務優先級 (1-5)
  "validation_level": "standard", // 驗證級別
  "user_id": "string",         // 用戶ID (可選)
  "metadata": {}               // 額外元數據
}
```

### 響應模型

#### SearchResponse

```json
{
  "job_id": "string",
  "message": "string",
  "estimated_completion_time": 30,
  "target_platforms": ["string"],
  "region": "string"
}
```

#### JobStatusResponse

```json
{
  "job_id": "string",
  "status": "string",
  "created_at": "string",
  "query": "string",
  "location": "string",
  "region": "string",
  "target_platforms": ["string"],
  "platform_status": {},
  "integrity_status": {},
  "total_jobs": 0,
  "execution_time": 0.0
}
```

## ⚙️ 配置說明

### 平台配置

每個平台都可以獨立配置以下參數：

- `enabled`: 是否啟用平台
- `max_concurrent_requests`: 最大併發請求數
- `timeout_seconds`: 請求超時時間
- `retry_attempts`: 重試次數
- `rate_limit_per_minute`: 每分鐘請求限制
- `priority`: 平台優先級

### 地區配置

每個地區可以配置：

- `primary_platforms`: 主要平台列表
- `fallback_platforms`: 後備平台列表
- `timezone`: 時區
- `language`: 語言
- `location_keywords`: 位置關鍵詞

### 調度器配置

- `max_concurrent_jobs`: 最大併發任務數
- `max_queue_size`: 最大隊列大小
- `job_timeout_minutes`: 任務超時時間
- `retry_failed_jobs`: 是否重試失敗任務

## 🔧 高級功能

### 1. 自定義平台

```python
# 添加新平台配置
from multi_platform_config import get_config

config = get_config()
config.platforms["new_platform"] = PlatformConfig(
    name="new_platform",
    enabled=True,
    max_concurrent_requests=5,
    timeout_seconds=30
)
config.save_configs()
```

### 2. 自定義地區

```python
# 添加新地區配置
config.regions["new_region"] = RegionConfig(
    name="new_region",
    display_name="新地區",
    primary_platforms=["platform1", "platform2"],
    timezone="Asia/Shanghai",
    language="zh-CN"
)
config.save_configs()
```

### 3. 事件處理

```python
# 註冊自定義事件處理器
async def custom_event_handler(event):
    print(f"處理事件: {event.event_type}")

api.sync_manager.register_event_handler(
    SyncEventType.JOB_COMPLETED,
    custom_event_handler
)
```

## 📈 監控和日誌

### 系統監控

- 任務執行狀態監控
- 平台健康狀況監控
- 系統性能指標監控
- 錯誤率和成功率統計

### 日誌記錄

系統使用結構化日誌記錄，支援多個日誌級別：

- `DEBUG`: 詳細調試信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 錯誤信息
- `CRITICAL`: 嚴重錯誤

## 🧪 測試

### 單元測試

```bash
# 運行所有測試
python -m pytest tests/

# 運行特定測試
python -m pytest tests/test_multi_platform_scheduler.py
```

### 集成測試

```bash
# 運行演示腳本進行集成測試
python example_multi_platform_usage.py
```

### 性能測試

```bash
# 使用Apache Bench進行性能測試
ab -n 1000 -c 10 -H "Content-Type: application/json" \
   -p search_request.json http://localhost:8000/search
```

## 🚨 故障排除

### 常見問題

1. **Redis連接失敗**
   - 檢查Redis服務是否運行
   - 驗證連接參數
   - 檢查防火牆設置

2. **任務執行超時**
   - 增加任務超時時間
   - 檢查平台響應時間
   - 調整併發數量

3. **平台選擇錯誤**
   - 檢查地區配置
   - 驗證位置關鍵詞
   - 確認平台啟用狀態

### 調試模式

```bash
# 啟用調試模式
export CONFIG_LEVEL=development
python integrated_multi_platform_api.py
```

## 📚 相關文檔

- [智能路由指南](docs/INTELLIGENT_ROUTING_GUIDE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [LLM JSON處理架構](LLM_JSON_PROCESSING_ARCHITECTURE.md)
- [API參考文檔](http://localhost:8000/docs)

## 🤝 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 許可證

本項目採用 MIT 許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 👥 作者

- JobSpy Team
- 聯繫方式: [your-email@example.com]

## 🙏 致謝

感謝所有為此項目做出貢獻的開發者和測試人員。

---

**注意**: 本系統仍在積極開發中，某些功能可能會發生變化。請定期查看文檔更新。