# LiteLLM Docker 代理服務器部署指南

## 📋 概述

LiteLLM是一個強大的LLM代理服務器，可以統一調用多個LLM提供商的API，包括OpenAI、Anthropic、DeepSeek、Google等。通過Docker部署，您可以快速搭建一個統一的LLM API網關。

## 🎯 主要功能

- **統一API接口** - 使用OpenAI格式調用所有LLM提供商
- **負載均衡** - 自動在多個模型間分配請求
- **故障轉移** - 當一個API不可用時自動切換到備用API
- **速率限制** - 控制每個模型的請求頻率
- **使用監控** - 追蹤API使用情況和成本
- **緩存支持** - 減少重複請求的成本

## 🚀 快速開始

### 1. 前置要求

- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- 至少一個LLM API密鑰 (OpenAI、Anthropic、DeepSeek等)

### 2. 設置API密鑰

在PowerShell中設置環境變量：

```powershell
# 設置API密鑰
$env:OPENAI_API_KEY="your-openai-api-key"
$env:ANTHROPIC_API_KEY="your-anthropic-api-key"
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"
$env:GOOGLE_API_KEY="your-google-api-key"
```

### 3. 啟動服務

#### 方法一：使用啟動腳本（推薦）

```batch
# 雙擊運行或在命令行執行
start_litellm_docker.bat
```

#### 方法二：手動啟動

```bash
# 啟動所有服務
docker compose -f docker-compose.litellm.yml up -d

# 查看日誌
docker compose -f docker-compose.litellm.yml logs -f litellm-proxy

# 停止服務
docker compose -f docker-compose.litellm.yml down
```

### 4. 驗證部署

```bash
# 運行測試腳本
python test_litellm_docker.py
```

## 🔧 配置說明

### litellm_config.yaml

主要配置文件，定義了可用的模型和路由策略：

```yaml
model_list:
  # OpenAI 模型
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      rpm: 60

  # Anthropic 模型
  - model_name: claude-3-haiku
    litellm_params:
      model: anthropic/claude-3-haiku-20240307
      api_key: os.environ/ANTHROPIC_API_KEY
      rpm: 60

  # DeepSeek 模型
  - model_name: deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: os.environ/DEEPSEEK_API_KEY
      api_base: https://api.deepseek.com
      rpm: 60
```

### docker-compose.litellm.yml

Docker Compose配置，包含：
- **litellm-proxy** - 主要的代理服務
- **redis** - 緩存服務（可選）
- **postgres** - 數據庫服務（可選）

## 🌐 API 使用

### 健康檢查

```bash
curl http://localhost:4000/health
```

### 獲取模型列表

```bash
curl http://localhost:4000/v1/models
```

### 聊天完成

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-master-key" \
  -d '{
    "model": "claude-3-haiku",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }'
```

### Python 客戶端示例

```python
import openai

# 配置客戶端指向LiteLLM代理
client = openai.OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-litellm-master-key"
)

# 使用任何配置的模型
response = client.chat.completions.create(
    model="claude-3-haiku",  # 或 "deepseek-chat", "gpt-4o" 等
    messages=[
        {"role": "user", "content": "你好，請介紹一下你自己"}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
```

## 🔍 監控和管理

### Web UI

訪問 http://localhost:4000 查看Web管理界面，可以：
- 查看模型狀態
- 監控API使用情況
- 管理用戶和密鑰
- 查看日誌和統計

### 日誌查看

```bash
# 查看實時日誌
docker compose -f docker-compose.litellm.yml logs -f litellm-proxy

# 查看特定時間的日誌
docker compose -f docker-compose.litellm.yml logs --since="1h" litellm-proxy
```

### 性能監控

```bash
# 查看容器資源使用
docker stats litellm-proxy

# 查看容器詳細信息
docker inspect litellm-proxy
```

## 🛠️ 故障排除

### 常見問題

1. **容器啟動失敗**
   ```bash
   # 檢查Docker是否運行
   docker version
   
   # 檢查端口是否被占用
   netstat -an | findstr :4000
   ```

2. **API調用失敗**
   ```bash
   # 檢查API密鑰是否正確設置
   docker compose -f docker-compose.litellm.yml exec litellm-proxy env | grep API_KEY
   
   # 檢查配置文件
   docker compose -f docker-compose.litellm.yml exec litellm-proxy cat /app/config.yaml
   ```

3. **模型不可用**
   - 確認API密鑰有效
   - 檢查API配額是否用完
   - 驗證模型名稱是否正確

### 調試模式

啟用詳細日誌：

```yaml
# 在docker-compose.litellm.yml中添加
environment:
  - LITELLM_LOG=DEBUG
```

## 🔒 安全考慮

1. **更改默認密鑰**
   ```yaml
   environment:
     - LITELLM_MASTER_KEY=your-secure-master-key
   ```

2. **限制網絡訪問**
   ```yaml
   ports:
     - "127.0.0.1:4000:4000"  # 只允許本地訪問
   ```

3. **使用HTTPS**
   - 在生產環境中配置反向代理（如Nginx）
   - 使用SSL證書加密通信

## 📚 進階配置

### 負載均衡

```yaml
router_settings:
  routing_strategy: "least-busy"  # 或 "simple-shuffle", "latency-based"
  model_group_alias:
    gpt-4: ["gpt-4o", "gpt-4-turbo"]
    claude: ["claude-3-haiku", "claude-3-sonnet"]
```

### 速率限制

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      rpm: 60        # 每分鐘請求數
      tpm: 100000    # 每分鐘token數
```

### 緩存配置

```yaml
router_settings:
  redis_host: redis
  redis_port: 6379
  cache_responses: true
  cache_kwargs:
    ttl: 3600  # 緩存1小時
```

## 🤝 整合到JobSpy

在JobSpy專案中使用LiteLLM代理：

```python
# 修改jobseeker/litellm_client.py
class LiteLLMClient:
    def __init__(self, base_url="http://localhost:4000/v1", api_key="sk-litellm-master-key"):
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key
        )
    
    def call(self, model, messages, **kwargs):
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
```

## 📞 支持和資源

- **官方文檔**: https://docs.litellm.ai/
- **GitHub**: https://github.com/BerriAI/litellm
- **Discord社群**: https://discord.gg/wuPM9dRgDw
- **問題回報**: https://github.com/BerriAI/litellm/issues

---

**注意**: 這是一個開發環境配置。在生產環境中，請確保適當的安全措施、監控和備份策略。