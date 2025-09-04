# LLM指令遵循與結構化輸出標準庫

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)]()

一個統一的Python庫，用於實現跨多個大型語言模型（LLM）提供商的指令遵循和結構化輸出標準化。

## 🌟 特性

- **🔄 統一接口**: 為OpenAI、Anthropic、Google、DeepSeek等提供商提供一致的API
- **📋 標準化指令**: 定義清晰的指令格式和輸出結構
- **✅ 自動驗證**: 內置JSON Schema驗證和響應格式檢查
- **🔄 故障轉移**: 自動負載均衡和故障轉移機制
- **📊 性能監控**: 詳細的性能指標和使用統計
- **🛡️ 錯誤處理**: 完善的錯誤處理和重試機制
- **⚙️ 靈活配置**: 支持多種配置方式和自定義選項
- **🚀 異步支持**: 支持異步操作和批量處理
- **📝 豐富日誌**: 結構化日誌和調試信息
- **🔧 命令行工具**: 便捷的CLI工具用於測試和管理

## 📦 安裝

### 基礎安裝

```bash
pip install llm-instruction-standard
```

### 完整安裝（包含所有可選依賴）

```bash
pip install llm-instruction-standard[all]
```

### 開發環境安裝

```bash
git clone https://github.com/jobspy/llm-instruction-standard.git
cd llm-instruction-standard
pip install -e .[dev]
```

## 🚀 快速開始

### 基本使用

```python
from llm_standard import StandardLLMClient

# 創建客戶端
client = StandardLLMClient(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4"
)

# 創建指令
instruction = client.create_instruction(
    instruction_type="structured_output",
    description="分析用戶評論的情感",
    output_schema={
        "type": "object",
        "properties": {
            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "keywords": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["sentiment", "confidence"]
    }
)

# 執行指令
response = client.execute(instruction, "這個產品真的很棒，我非常滿意！")

if response['status'] == 'success':
    data = response['data']
    print(f"情感: {data['sentiment']}")
    print(f"置信度: {data['confidence']}")
    print(f"關鍵詞: {data.get('keywords', [])}")
else:
    print(f"錯誤: {response['errors']}")
```

### 客戶端池和負載均衡

```python
from llm_standard import StandardLLMClient
from llm_standard.client import LLMClientPool

# 創建多個客戶端
clients = [
    StandardLLMClient(provider="openai", api_key="key1", model="gpt-4"),
    StandardLLMClient(provider="anthropic", api_key="key2", model="claude-3-haiku"),
    StandardLLMClient(provider="deepseek", api_key="key3", model="deepseek-chat")
]

# 創建客戶端池
pool = LLMClientPool(clients)

# 使用池執行指令（自動負載均衡和故障轉移）
response = pool.execute(instruction, "分析這段文本")
```

### 批量處理

```python
# 批量處理多個輸入
inputs = [
    "這個產品很好用",
    "服務態度一般",
    "價格太貴了",
    "質量不錯，推薦購買"
]

responses = client.batch_execute(instruction, inputs)

for i, response in enumerate(responses):
    if response['status'] == 'success':
        print(f"輸入 {i+1}: {response['data']['sentiment']}")
```

## 📋 指令格式標準

### 標準指令結構

```json
{
  "instruction_type": "structured_output",
  "version": "1.0",
  "task": {
    "description": "任務描述",
    "context": "任務上下文（可選）",
    "constraints": ["約束條件1", "約束條件2"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "field1": {"type": "string"},
      "field2": {"type": "integer"}
    },
    "required": ["field1"]
  },
  "examples": [
    {
      "input": "示例輸入",
      "output": {"field1": "示例輸出"}
    }
  ],
  "metadata": {
    "priority": "high",
    "timeout": 30,
    "retry_count": 3
  }
}
```

### 支持的指令類型

- `structured_output`: 結構化輸出
- `text_analysis`: 文本分析
- `extraction`: 信息提取
- `classification`: 文本分類
- `summarization`: 文本摘要
- `generation`: 文本生成
- `translation`: 文本翻譯
- `question_answering`: 問答

## 🔧 配置管理

### 環境變量配置

```bash
# OpenAI配置
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4"

# Anthropic配置
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-3-haiku-20240307"

# Google配置
export GOOGLE_API_KEY="your-google-key"
export GOOGLE_MODEL="gemini-pro"

# DeepSeek配置
export DEEPSEEK_API_KEY="your-deepseek-key"
export DEEPSEEK_MODEL="deepseek-chat"

# 其他配置
export LLM_LOG_LEVEL="INFO"
export LLM_CACHE_ENABLED="true"
export LLM_VALIDATE_STRICT="true"
```

### 配置文件

```python
from llm_standard.config import StandardConfig

# 從文件加載配置
config = StandardConfig.from_file("config.json")

# 從環境變量加載配置
config = StandardConfig.from_env()

# 設置全局配置
from llm_standard.config import set_config
set_config(config)
```

### 配置文件示例 (config.json)

```json
{
  "models": {
    "openai": {
      "provider": "openai",
      "model": "gpt-4",
      "api_key": "your-api-key",
      "max_tokens": 4000,
      "temperature": 0.7,
      "timeout": 30
    },
    "anthropic": {
      "provider": "anthropic",
      "model": "claude-3-haiku-20240307",
      "api_key": "your-api-key",
      "max_tokens": 4000,
      "temperature": 0.7
    }
  },
  "validation": {
    "validate_instructions": true,
    "validate_responses": true,
    "strict_schema": true
  },
  "logging": {
    "level": "INFO",
    "log_requests": false,
    "log_responses": false
  },
  "performance": {
    "enable_caching": true,
    "cache_ttl": 3600,
    "enable_metrics": true
  }
}
```

## 🖥️ 命令行工具

### 安裝後可用的CLI命令

```bash
# 測試連接
llm-standard test-connection --provider openai --api-key your-key

# 執行指令
llm-standard execute --provider openai --instruction-type structured_output \
  --description "分析情感" --schema-file schema.json "這是一段測試文本"

# 性能基準測試
llm-standard benchmark --providers openai anthropic --iterations 10

# 初始化配置文件
llm-standard init-config --output my-config.json

# 驗證JSON Schema
llm-standard validate-schema --schema-file schema.json --data-file data.json
```

### CLI使用示例

```bash
# 測試OpenAI連接
llm-standard test-connection -p openai -k sk-your-api-key -m gpt-4

# 執行文本分析
llm-standard execute -p openai -t text_analysis \
  -d "分析這段文本的情感" \
  "我對這個產品非常滿意，質量很好！"

# 批量性能測試
llm-standard benchmark -p openai anthropic deepseek -n 20 --concurrent 3
```

## 📊 性能監控

### 內置指標

```python
# 獲取客戶端統計信息
stats = client.get_stats()
print(f"總請求數: {stats['total_requests']}")
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均響應時間: {stats['avg_response_time']:.2f}秒")
print(f"總Token使用: {stats['total_tokens']}")

# 健康檢查
health = client.health_check()
if health['status'] == 'healthy':
    print("客戶端狀態正常")
else:
    print(f"客戶端異常: {health['error']}")
```

### 性能分析

```python
# 啟用性能分析
client = StandardLLMClient(
    provider="openai",
    api_key="your-key",
    model="gpt-4",
    enable_profiling=True
)

# 執行後查看性能報告
response = client.execute(instruction, "測試文本")
profile = response['metadata']['performance_profile']
print(f"API調用時間: {profile['api_call_time']:.2f}秒")
print(f"驗證時間: {profile['validation_time']:.2f}秒")
print(f"總處理時間: {profile['total_time']:.2f}秒")
```

## 🛡️ 錯誤處理

### 異常類型

```python
from llm_standard.exceptions import (
    InvalidInputError,
    SchemaValidationError,
    TokenLimitExceededError,
    ProviderError,
    TimeoutError,
    RateLimitError
)

try:
    response = client.execute(instruction, "測試輸入")
except InvalidInputError as e:
    print(f"輸入無效: {e.message}")
    print(f"錯誤字段: {e.details['field']}")
except SchemaValidationError as e:
    print(f"Schema驗證失敗: {e.message}")
    for error in e.details['validation_errors']:
        print(f"  - {error['path']}: {error['message']}")
except TokenLimitExceededError as e:
    print(f"Token限制超出: {e.details['current_tokens']}/{e.details['max_tokens']}")
except ProviderError as e:
    print(f"提供商錯誤: {e.message}")
    print(f"狀態碼: {e.details['status_code']}")
except TimeoutError as e:
    print(f"請求超時: {e.message}")
except RateLimitError as e:
    print(f"速率限制: {e.message}")
    print(f"重試時間: {e.details['retry_after']}秒")
```

### 重試機制

```python
# 配置重試策略
client = StandardLLMClient(
    provider="openai",
    api_key="your-key",
    model="gpt-4",
    retry_count=3,
    retry_delay=1.0,
    retry_on_timeout=True,
    retry_on_rate_limit=True
)
```

## 🧪 測試

### 運行測試

```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/test_client.py

# 運行測試並生成覆蓋率報告
pytest --cov=llm_standard --cov-report=html

# 運行性能測試
pytest tests/test_performance.py -v
```

### 測試配置

```python
# tests/conftest.py
import pytest
from llm_standard import StandardLLMClient

@pytest.fixture
def mock_client():
    return StandardLLMClient(
        provider="openai",
        api_key="test-key",
        model="gpt-4"
    )
```

## 📚 高級用法

### 自定義適配器

```python
from llm_standard.adapters import BaseLLMAdapter

class CustomAdapter(BaseLLMAdapter):
    def convert_instruction(self, instruction, user_input):
        # 自定義指令轉換邏輯
        pass
    
    def call_api(self, converted_instruction):
        # 自定義API調用邏輯
        pass
    
    def parse_response(self, api_response):
        # 自定義響應解析邏輯
        pass

# 註冊自定義適配器
client = StandardLLMClient(
    provider="custom",
    adapter=CustomAdapter(),
    api_key="your-key"
)
```

### 自定義驗證器

```python
from llm_standard.validators import SchemaValidator

class CustomValidator(SchemaValidator):
    def validate_custom_format(self, value, format_name):
        if format_name == "custom-id":
            return value.startswith("ID_") and len(value) == 10
        return super().validate_custom_format(value, format_name)

# 使用自定義驗證器
validator = CustomValidator()
client = StandardLLMClient(
    provider="openai",
    api_key="your-key",
    validator=validator
)
```

### 緩存配置

```python
from llm_standard.cache import RedisCache

# 使用Redis緩存
cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    ttl=3600
)

client = StandardLLMClient(
    provider="openai",
    api_key="your-key",
    cache=cache
)
```

## 🤝 貢獻

我們歡迎社區貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何參與。

### 開發環境設置

```bash
# 克隆倉庫
git clone https://github.com/jobspy/llm-instruction-standard.git
cd llm-instruction-standard

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝開發依賴
pip install -e .[dev]

# 安裝pre-commit鉤子
pre-commit install

# 運行測試
pytest
```

### 代碼規範

```bash
# 代碼格式化
black llm_standard/
isort llm_standard/

# 代碼檢查
flake8 llm_standard/
mypy llm_standard/

# 運行所有檢查
pre-commit run --all-files
```

## 📄 許可證

本項目採用 MIT 許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 🆘 支持

- 📖 [文檔](https://llm-instruction-standard.readthedocs.io/)
- 🐛 [問題追蹤](https://github.com/jobspy/llm-instruction-standard/issues)
- 💬 [討論區](https://github.com/jobspy/llm-instruction-standard/discussions)
- 📧 [郵件支持](mailto:support@jobspy.com)

## 🗺️ 路線圖

- [ ] 支持更多LLM提供商（Cohere、Hugging Face等）
- [ ] 實現流式響應支持
- [ ] 添加圖像和多模態輸入支持
- [ ] 開發Web界面和管理控制台
- [ ] 實現分布式部署支持
- [ ] 添加A/B測試功能
- [ ] 集成更多監控和分析工具

## 📊 統計

![GitHub stars](https://img.shields.io/github/stars/jobspy/llm-instruction-standard?style=social)
![GitHub forks](https://img.shields.io/github/forks/jobspy/llm-instruction-standard?style=social)
![GitHub issues](https://img.shields.io/github/issues/jobspy/llm-instruction-standard)
![GitHub pull requests](https://img.shields.io/github/issues-pr/jobspy/llm-instruction-standard)

---

**由 [JobSpy Team](https://github.com/jobspy) 開發和維護**