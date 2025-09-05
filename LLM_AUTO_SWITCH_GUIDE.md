# LLM 自動切換功能使用指南

## 概述

LLM 自動切換功能是一個智能的多 LLM 提供商管理系統，能夠在預設 LLM 餘額不足或失效時自動切換到備用 LLM，確保服務的連續性和可靠性。

## 功能特點

### 🔄 自動切換機制
- **錯誤檢測**: 自動檢測 API 配額超出、認證失敗、速率限制等錯誤
- **智能切換**: 根據提供商健康狀況自動選擇最佳備用提供商
- **無縫體驗**: 切換過程對用戶透明，不影響正常使用

### 📊 狀態監控
- **實時狀態**: 監控所有 LLM 提供商的健康狀況
- **性能統計**: 追蹤成功率、響應時間、錯誤次數等指標
- **歷史記錄**: 記錄切換事件和錯誤日誌

### 🎛️ 手動控制
- **手動切換**: 支援手動切換到指定的 LLM 提供商
- **狀態查詢**: 提供 API 端點查詢當前系統狀態
- **提供商管理**: 獲取可用提供商列表和配置信息

## 支援的 LLM 提供商

| 提供商 | 狀態 | 說明 |
|--------|------|------|
| OpenAI | ✅ 支援 | GPT-3.5, GPT-4 系列 |
| Anthropic | ✅ 支援 | Claude 系列 |
| Google AI | ✅ 支援 | Gemini 系列 |
| Azure OpenAI | ⚠️ 需配置 | 需要額外的 Azure 配置 |
| DeepSeeker | ⚠️ 需配置 | 需要相應的 API 密鑰 |
| OpenRouter | ⚠️ 需配置 | 統一 API 接口 |
| Local LLaMA | ✅ 支援 | 本地部署模型 |

## 環境變數配置

在 `.env` 文件中配置以下環境變數：

```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Anthropic 配置
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Google AI 配置
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-pro

# Azure OpenAI 配置（可選）
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_VERSION=2023-12-01-preview

# DeepSeeker 配置（可選）
DEEPSEEKER_API_KEY=your_deepseeker_api_key

# OpenRouter 配置（可選）
OPENROUTER_API_KEY=your_openrouter_api_key
```

## API 端點

### 1. 獲取 LLM 狀態

```http
GET /api/llm-status
```

**響應示例:**
```json
{
  "status": {
    "auto_switch_enabled": true,
    "current_provider": "openai",
    "total_calls": 150,
    "total_errors": 5,
    "total_switches": 2,
    "success_rate": 0.967,
    "provider_status": {
      "openai": {
        "is_healthy": true,
        "success_rate": 0.95,
        "consecutive_failures": 0,
        "last_success": "2025-01-27T10:30:00Z",
        "total_calls": 100,
        "total_errors": 5
      },
      "anthropic": {
        "is_healthy": true,
        "success_rate": 0.98,
        "consecutive_failures": 0,
        "last_success": "2025-01-27T10:25:00Z",
        "total_calls": 50,
        "total_errors": 1
      }
    },
    "recent_switches": [
      {
        "timestamp": "2025-01-27T09:15:00Z",
        "from_provider": "openai",
        "to_provider": "anthropic",
        "reason": "配額超出",
        "error_type": "quota_exceeded"
      }
    ]
  }
}
```

### 2. 手動切換提供商

```http
POST /api/llm-switch
Content-Type: application/json

{
  "provider": "anthropic"
}
```

**響應示例:**
```json
{
  "success": true,
  "message": "成功切換到 anthropic",
  "current_provider": "anthropic"
}
```

### 3. 獲取可用提供商

```http
GET /api/llm-providers
```

**響應示例:**
```json
{
  "success": true,
  "providers": ["openai", "anthropic", "google", "local_llama"]
}
```

## 程式碼使用示例

### 基本使用

```python
from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer
from jobseeker.llm_config import LLMProvider

# 初始化帶自動切換的意圖分析器
analyzer = LLMIntentAnalyzer(
    provider=LLMProvider.OPENAI,
    enable_auto_switch=True,  # 啟用自動切換
    fallback_to_basic=True    # 啟用基礎分析器作為最後備選
)

# 正常使用，系統會自動處理錯誤和切換
result = analyzer.analyze_intent_with_decision("找軟體工程師工作")
print(result)
```

### 狀態監控

```python
# 獲取系統狀態
status = analyzer.get_llm_status()
print(f"當前提供商: {status['current_provider']}")
print(f"自動切換啟用: {status['auto_switch_enabled']}")

# 獲取可用提供商
providers = analyzer.get_available_providers()
print(f"可用提供商: {providers}")
```

### 手動切換

```python
# 手動切換到指定提供商
success = analyzer.switch_provider("anthropic")
if success:
    print("切換成功")
else:
    print("切換失敗")
```

## 錯誤處理機制

### 支援的錯誤類型

1. **配額超出** (`quota_exceeded`)
   - OpenAI: "You exceeded your current quota"
   - 自動切換到其他可用提供商

2. **認證失敗** (`authentication_error`)
   - 無效的 API 密鑰
   - 標記提供商為不健康狀態

3. **速率限制** (`rate_limit_exceeded`)
   - API 調用頻率過高
   - 短暫等待後重試或切換提供商

4. **服務不可用** (`service_unavailable`)
   - 提供商服務暫時不可用
   - 自動切換到備用提供商

5. **網路錯誤** (`network_error`)
   - 連接超時或網路問題
   - 重試機制和自動切換

### 切換策略

1. **健康狀況優先**: 優先選擇健康狀況良好的提供商
2. **成功率考量**: 考慮歷史成功率選擇最可靠的提供商
3. **負載均衡**: 避免過度依賴單一提供商
4. **回退機制**: 最終回退到基礎分析器確保服務可用性

## 監控和維護

### 日誌監控

系統會記錄以下日誌信息：
- 提供商切換事件
- API 調用錯誤
- 健康檢查結果
- 性能統計更新

### 定期檢查

建議定期檢查以下項目：
1. **API 密鑰有效性**: 確保所有配置的 API 密鑰仍然有效
2. **配額使用情況**: 監控各提供商的配額使用情況
3. **錯誤率統計**: 檢查錯誤率是否在正常範圍內
4. **切換頻率**: 避免過於頻繁的切換

### 性能優化

1. **緩存策略**: 啟用緩存減少重複 API 調用
2. **超時設置**: 合理設置 API 調用超時時間
3. **重試機制**: 配置適當的重試次數和延遲
4. **健康檢查**: 定期進行健康檢查維護提供商狀態

## 故障排除

### 常見問題

1. **自動切換未啟用**
   - 檢查 `enable_auto_switch=True` 是否正確設置
   - 確認至少配置了兩個有效的 LLM 提供商

2. **提供商配置無效**
   - 檢查環境變數是否正確設置
   - 驗證 API 密鑰的有效性

3. **切換失敗**
   - 檢查目標提供商是否健康
   - 查看日誌了解具體錯誤原因

4. **性能問題**
   - 檢查網路連接狀況
   - 調整超時和重試設置

### 測試工具

使用提供的測試腳本驗證功能：

```bash
python test_llm_auto_switch.py
```

## 最佳實踐

1. **多提供商配置**: 至少配置 2-3 個不同的 LLM 提供商
2. **密鑰管理**: 定期輪換 API 密鑰，避免配額耗盡
3. **監控告警**: 設置監控告警及時發現問題
4. **測試驗證**: 定期測試自動切換功能確保正常工作
5. **文檔更新**: 保持配置文檔和使用說明的更新

## 更新日誌

### v1.0.0 (2025-01-27)
- ✅ 實現基本的自動切換功能
- ✅ 支援多種錯誤類型檢測
- ✅ 提供 REST API 端點
- ✅ 實現狀態監控和手動切換
- ✅ 完整的測試覆蓋和文檔

---

**注意**: 這是一個生產就緒的功能，但建議在正式環境使用前進行充分的測試和驗證。