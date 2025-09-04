# LLM指令遵循與結構化輸出標準規範

## 概述

本文檔定義了一套統一的標準規範，用於確保不同LLM提供商在指令遵循和結構化JSON輸出方面的兼容性和一致性。

## 版本信息

- **版本**: 1.0.0
- **發布日期**: 2025-01-05
- **適用範圍**: 所有支持的LLM提供商（OpenAI、Anthropic、Google、DeepSeek等）

## 1. 指令格式標準

### 1.1 基本指令結構

所有指令必須遵循以下JSON格式：

```json
{
  "instruction_type": "structured_output",
  "version": "1.0",
  "task": {
    "description": "任務描述",
    "context": "上下文信息（可選）",
    "constraints": ["約束條件列表"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      // JSON Schema定義
    },
    "required": ["必填字段列表"]
  },
  "examples": [
    {
      "input": "示例輸入",
      "output": {"示例輸出"}
    }
  ],
  "metadata": {
    "priority": "high|medium|low",
    "timeout": 30,
    "retry_count": 3
  }
}
```

### 1.2 指令類型定義

- `structured_output`: 要求結構化JSON輸出
- `text_generation`: 純文本生成
- `analysis`: 分析任務
- `extraction`: 信息提取
- `classification`: 分類任務
- `summarization`: 摘要生成

### 1.3 約束條件規範

```json
"constraints": [
  "output_language: zh-CN",
  "max_tokens: 1000",
  "format: json_only",
  "validation: strict",
  "encoding: utf-8"
]
```

## 2. 輸出JSON結構規範

### 2.1 標準響應格式

所有LLM響應必須遵循以下統一格式：

```json
{
  "status": "success|error|partial",
  "timestamp": "2025-01-05T10:30:00Z",
  "model_info": {
    "provider": "openai|anthropic|google|deepseek",
    "model": "模型名稱",
    "version": "模型版本"
  },
  "request_id": "唯一請求標識符",
  "data": {
    // 實際輸出數據，遵循請求中的output_schema
  },
  "metadata": {
    "processing_time": 1.23,
    "token_usage": {
      "prompt_tokens": 100,
      "completion_tokens": 200,
      "total_tokens": 300
    },
    "confidence_score": 0.95
  },
  "errors": [
    // 錯誤信息（如果有）
  ],
  "warnings": [
    // 警告信息（如果有）
  ]
}
```

### 2.2 數據類型標準

| 類型 | 格式 | 示例 | 驗證規則 |
|------|------|------|----------|
| 字符串 | string | "示例文本" | 長度限制、編碼檢查 |
| 數字 | number | 123.45 | 範圍檢查、精度限制 |
| 布爾值 | boolean | true/false | 嚴格布爾類型 |
| 日期時間 | string | "2025-01-05T10:30:00Z" | ISO 8601格式 |
| 數組 | array | [1, 2, 3] | 長度限制、元素類型檢查 |
| 對象 | object | {"key": "value"} | 嵌套深度限制 |

### 2.3 字段命名規範

- 使用snake_case命名風格
- 字段名稱必須是英文
- 避免使用保留關鍵字
- 字段名稱應具有描述性

```json
// 正確示例
{
  "user_name": "張三",
  "created_at": "2025-01-05T10:30:00Z",
  "is_active": true,
  "contact_info": {
    "email": "user@example.com",
    "phone_number": "+86-138-0013-8000"
  }
}
```

## 3. 錯誤處理機制

### 3.1 錯誤代碼標準

| 錯誤代碼 | 錯誤類型 | 描述 | 處理建議 |
|----------|----------|------|----------|
| E001 | INVALID_INPUT | 輸入格式錯誤 | 檢查輸入格式 |
| E002 | SCHEMA_VALIDATION_FAILED | Schema驗證失敗 | 修正輸出格式 |
| E003 | TOKEN_LIMIT_EXCEEDED | 超出token限制 | 減少輸入長度 |
| E004 | TIMEOUT | 請求超時 | 重試或調整超時設置 |
| E005 | MODEL_UNAVAILABLE | 模型不可用 | 切換到備用模型 |
| E006 | RATE_LIMIT_EXCEEDED | 超出速率限制 | 實施退避重試 |
| E007 | CONTENT_FILTERED | 內容被過濾 | 修改輸入內容 |
| E008 | PARSING_ERROR | 解析錯誤 | 檢查輸出格式 |

### 3.2 錯誤響應格式

```json
{
  "status": "error",
  "timestamp": "2025-01-05T10:30:00Z",
  "request_id": "req_123456789",
  "errors": [
    {
      "code": "E002",
      "message": "Schema驗證失敗",
      "details": "字段'user_name'缺失",
      "field": "user_name",
      "severity": "error"
    }
  ],
  "suggested_actions": [
    "請確保所有必填字段都已提供",
    "檢查字段名稱是否正確"
  ]
}
```

### 3.3 重試機制

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "base_delay": 1.0,
    "max_delay": 60.0,
    "retry_on_errors": ["E004", "E005", "E006"]
  }
}
```

## 4. 兼容性保證

### 4.1 提供商適配

每個LLM提供商需要實現統一的適配器接口：

```python
class LLMAdapter:
    def format_instruction(self, standard_instruction: dict) -> str:
        """將標準指令格式轉換為提供商特定格式"""
        pass
    
    def parse_response(self, raw_response: str) -> dict:
        """將提供商響應解析為標準格式"""
        pass
    
    def validate_output(self, output: dict, schema: dict) -> bool:
        """驗證輸出是否符合Schema"""
        pass
```

### 4.2 版本兼容性

- 向後兼容：新版本必須支持舊版本的指令格式
- 版本標識：每個請求必須包含版本信息
- 遷移指南：提供版本升級的詳細指南

### 4.3 功能支持矩陣

| 功能 | OpenAI | Anthropic | Google | DeepSeek |
|------|--------|-----------|--------|---------|
| 結構化輸出 | ✅ | ✅ | ✅ | ✅ |
| JSON Schema驗證 | ✅ | ✅ | ⚠️ | ✅ |
| 函數調用 | ✅ | ✅ | ✅ | ❌ |
| 流式輸出 | ✅ | ✅ | ✅ | ✅ |
| 多模態輸入 | ✅ | ✅ | ✅ | ❌ |

## 5. 實施指南

### 5.1 集成步驟

1. **安裝依賴**
   ```bash
   pip install llm-instruction-standard
   ```

2. **初始化適配器**
   ```python
   from llm_standard import StandardLLMClient
   
   client = StandardLLMClient(
       provider="openai",
       api_key="your-api-key",
       model="gpt-4"
   )
   ```

3. **發送標準指令**
   ```python
   instruction = {
       "instruction_type": "structured_output",
       "version": "1.0",
       "task": {
           "description": "提取用戶信息"
       },
       "output_schema": {
           "type": "object",
           "properties": {
               "name": {"type": "string"},
               "age": {"type": "number"}
           }
       }
   }
   
   response = client.execute(instruction, input_text="我叫張三，今年25歲")
   ```

### 5.2 最佳實踐

1. **Schema設計**
   - 保持Schema簡潔明確
   - 使用描述性字段名稱
   - 提供詳細的字段描述
   - 設置合理的驗證規則

2. **錯誤處理**
   - 實施完整的錯誤捕獲
   - 提供有意義的錯誤消息
   - 實現自動重試機制
   - 記錄詳細的錯誤日誌

3. **性能優化**
   - 使用連接池管理
   - 實施請求緩存
   - 監控響應時間
   - 優化token使用

### 5.3 測試驗證

```python
# 測試用例示例
def test_structured_output():
    instruction = create_test_instruction()
    response = client.execute(instruction, "測試輸入")
    
    assert response["status"] == "success"
    assert validate_schema(response["data"], instruction["output_schema"])
    assert response["metadata"]["confidence_score"] > 0.8
```

## 6. 監控與維護

### 6.1 性能指標

- 響應時間（P50, P95, P99）
- 成功率
- 錯誤率分布
- Token使用效率
- Schema驗證通過率

### 6.2 質量保證

- 自動化測試覆蓋率 > 90%
- 定期進行兼容性測試
- 監控輸出質量變化
- 用戶反饋收集與分析

### 6.3 更新機制

- 定期評估標準的有效性
- 收集社區反饋
- 發布更新公告
- 提供遷移工具

## 7. 附錄

### 7.1 完整示例

詳見 `examples/` 目錄中的示例代碼。

### 7.2 常見問題

詳見 `FAQ.md` 文檔。

### 7.3 更新日誌

詳見 `CHANGELOG.md` 文檔。

---

**聯繫方式**
- 項目倉庫：https://github.com/jobspy/llm-instruction-standard
- 問題反饋：https://github.com/jobspy/llm-instruction-standard/issues
- 郵箱：support@jobspy.dev