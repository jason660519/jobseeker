# LLM JSON調度器系統部署指南

## 概述

本指南提供了LLM JSON調度器系統的完整部署、配置和運維說明。該系統是一個企業級的智能任務調度和處理平台，專門用於處理LLM生成的JSON檔案。

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM JSON調度器系統                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 檔案監控器   │  │ 智能路由器   │  │ 任務調度器   │         │
│  │ FileWatcher │  │ SmartRouter │  │ Scheduler   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│           │               │               │                 │
│           └───────────────┼───────────────┘                 │
│                          │                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 工作線程池   │  │ Redis隊列   │  │ 結果處理器   │         │
│  │ WorkerPool  │  │ TaskQueue   │  │ ResultHandler│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│           │               │               │                 │
│           └───────────────┼───────────────┘                 │
│                          │                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ API服務器   │  │ 監控系統     │  │ 日誌管理     │         │
│  │ FastAPI     │  │ Monitor     │  │ Logging     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. 檔案監控器 (FileWatcher)
- **功能**: 實時監控指定目錄中的JSON檔案變化
- **技術**: Python watchdog庫
- **特性**: 支援多目錄監控、檔案過濾、事件去重

### 2. 智能路由器 (SmartRouter)
- **功能**: 根據檔案內容和元數據智能路由任務
- **技術**: 基於規則引擎和機器學習
- **特性**: 地理位置檢測、行業分類、優先級分配

### 3. 任務調度器 (Scheduler)
- **功能**: 管理任務生命週期和執行策略
- **技術**: 異步任務處理、優先級隊列
- **特性**: 負載均衡、故障恢復、性能監控

### 4. Redis隊列系統
- **功能**: 高性能任務隊列和狀態管理
- **技術**: Redis + aioredis
- **特性**: 持久化、集群支援、優先級隊列

### 5. API服務器
- **功能**: RESTful API和管理界面
- **技術**: FastAPI + Uvicorn
- **特性**: 自動文檔、認證授權、實時監控

## 系統需求

### 硬體需求

#### 最低配置
- **CPU**: 2核心 2.0GHz
- **記憶體**: 4GB RAM
- **儲存**: 20GB 可用空間
- **網路**: 100Mbps

#### 推薦配置
- **CPU**: 4核心 3.0GHz 或更高
- **記憶體**: 8GB RAM 或更高
- **儲存**: 100GB SSD
- **網路**: 1Gbps

#### 生產環境配置
- **CPU**: 8核心 3.5GHz 或更高
- **記憶體**: 16GB RAM 或更高
- **儲存**: 500GB NVMe SSD
- **網路**: 10Gbps
- **備份**: 定期備份策略

### 軟體需求

#### 作業系統
- **Linux**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Windows**: Windows 10 / Windows Server 2019+
- **macOS**: macOS 11.0+

#### 運行環境
- **Python**: 3.8+ (推薦 3.11)
- **Redis**: 6.0+ (推薦 7.0)
- **Docker**: 20.10+ (可選)
- **Docker Compose**: 2.0+ (可選)

## 快速部署

### 方法一：自動部署腳本

```bash
# 1. 下載部署腳本
python deploy_scheduler.py deploy --method local --redis-method docker

# 2. 啟動系統
./deployment/start_scheduler.sh  # Linux/macOS
# 或
.\deployment\start_scheduler.bat  # Windows
```

### 方法二：Docker Compose部署

```bash
# 1. 創建Docker配置
python deploy_scheduler.py deploy --method docker

# 2. 啟動容器
cd deployment
docker-compose up -d

# 3. 查看日誌
docker-compose logs -f
```

### 方法三：手動部署

#### 步驟1：環境準備

```bash
# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

#### 步驟2：Redis設置

```bash
# Docker方式
docker run -d --name scheduler-redis -p 6379:6379 redis:7-alpine

# 或本地安裝
# Ubuntu/Debian
sudo apt update && sudo apt install redis-server
sudo systemctl start redis

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

#### 步驟3：目錄結構

```bash
# 創建必要目錄
mkdir -p data/llm_generated/{raw,processed,archive,errors,temp}
mkdir -p logs
mkdir -p deployment
```

#### 步驟4：配置檔案

複製並編輯 `scheduler_config.json`：

```json
{
  "directories": {
    "watch_directory": "./data/llm_generated/raw",
    "output_directory": "./data/llm_generated/processed",
    "archive_directory": "./data/llm_generated/archive",
    "error_directory": "./data/llm_generated/errors"
  },
  "processing": {
    "mode": "hybrid",
    "max_workers": 10
  },
  "queue": {
    "type": "redis",
    "redis_url": "redis://localhost:6379/0"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8080
  }
}
```

#### 步驟5：啟動服務

```bash
# 啟動調度器API
python scheduler_api.py

# 或在背景執行
nohup python scheduler_api.py > logs/scheduler.log 2>&1 &
```

## 配置說明

### 核心配置項

#### 目錄配置
```json
"directories": {
  "watch_directory": "./data/llm_generated/raw",      // 監控目錄
  "output_directory": "./data/llm_generated/processed", // 輸出目錄
  "archive_directory": "./data/llm_generated/archive",  // 歸檔目錄
  "error_directory": "./data/llm_generated/errors",    // 錯誤目錄
  "temp_directory": "./data/llm_generated/temp"        // 臨時目錄
}
```

#### 處理模式配置
```json
"processing": {
  "mode": "hybrid",           // 處理模式: real_time, batch, hybrid
  "max_workers": 10,          // 最大工作線程數
  "batch_size": 50,           // 批處理大小
  "batch_timeout": 300,       // 批處理超時（秒）
  "retry_attempts": 3,        // 重試次數
  "retry_delay": 5            // 重試延遲（秒）
}
```

#### 隊列配置
```json
"queue": {
  "type": "redis",                    // 隊列類型: local, redis
  "redis_url": "redis://localhost:6379/0",
  "max_queue_size": 10000,            // 最大隊列大小
  "priority_levels": ["high", "medium", "low"]
}
```

#### API配置
```json
"api": {
  "host": "0.0.0.0",          // 綁定地址
  "port": 8080,               // 端口
  "workers": 4,               // Uvicorn工作進程數
  "reload": false,            // 開發模式重載
  "access_log": true          // 訪問日誌
}
```

### 高級配置

#### 智能路由配置
```json
"intelligent_routing": {
  "enabled": true,
  "geo_detection": true,
  "industry_classification": true,
  "priority_rules": {
    "urgent_keywords": ["urgent", "priority", "asap"],
    "low_priority_keywords": ["test", "demo", "sample"]
  }
}
```

#### 監控配置
```json
"monitoring": {
  "enabled": true,
  "metrics_retention_days": 30,
  "alert_thresholds": {
    "cpu_usage": 80.0,
    "memory_usage": 85.0,
    "queue_size": 1000,
    "error_rate": 10.0
  },
  "notification_channels": {
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-password",
      "recipients": ["admin@company.com"]
    },
    "slack": {
      "enabled": false,
      "webhook_url": "https://hooks.slack.com/services/..."
    }
  }
}
```

## 運維管理

### 日常監控

#### 實時監控
```bash
# 啟動實時監控
python monitor_scheduler.py monitor --interval 5

# 檢查當前狀態
python monitor_scheduler.py status

# 查看任務列表
python monitor_scheduler.py tasks --limit 100
```

#### 性能報告
```bash
# 生成24小時報告
python monitor_scheduler.py report --hours 24 --output daily_report.json

# 生成週報告
python monitor_scheduler.py report --hours 168 --output weekly_report.json
```

### 系統維護

#### 重啟服務
```bash
# 通過API重啟
python monitor_scheduler.py restart

# 或手動重啟
pkill -f scheduler_api.py
python scheduler_api.py
```

#### 清理數據
```bash
# 清理歸檔檔案（保留30天）
find ./data/llm_generated/archive -name "*.json" -mtime +30 -delete

# 清理日誌檔案（保留7天）
find ./logs -name "*.log" -mtime +7 -delete
```

#### 備份數據
```bash
# 備份配置和數據
tar -czf backup_$(date +%Y%m%d).tar.gz \
    scheduler_config.json \
    data/ \
    logs/

# 備份Redis數據
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb backup/redis_$(date +%Y%m%d).rdb
```

### 故障排除

#### 常見問題

1. **調度器無法啟動**
   ```bash
   # 檢查端口占用
   netstat -tulpn | grep 8080
   
   # 檢查Redis連接
   redis-cli ping
   
   # 查看錯誤日誌
   tail -f logs/scheduler.log
   ```

2. **任務處理緩慢**
   ```bash
   # 檢查系統資源
   top
   free -h
   df -h
   
   # 檢查隊列狀態
   redis-cli LLEN scheduler:queue:high
   redis-cli LLEN scheduler:queue:medium
   redis-cli LLEN scheduler:queue:low
   ```

3. **記憶體使用過高**
   ```bash
   # 檢查進程記憶體使用
   ps aux | grep python
   
   # 重啟服務釋放記憶體
   python monitor_scheduler.py restart
   ```

#### 日誌分析

```bash
# 查看錯誤日誌
grep "ERROR" logs/scheduler.log | tail -20

# 統計任務處理情況
grep "Task completed" logs/scheduler.log | wc -l
grep "Task failed" logs/scheduler.log | wc -l

# 分析性能瓶頸
grep "Processing time" logs/scheduler.log | awk '{print $NF}' | sort -n
```

## 性能優化

### 系統調優

#### 1. 工作線程優化
```json
{
  "processing": {
    "max_workers": "auto",  // 自動根據CPU核心數設置
    "worker_timeout": 300,   // 工作線程超時
    "queue_timeout": 60      // 隊列等待超時
  }
}
```

#### 2. Redis優化
```bash
# Redis配置優化
echo "maxmemory 2gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
echo "save 900 1" >> /etc/redis/redis.conf
sudo systemctl restart redis
```

#### 3. 系統參數調優
```bash
# 增加檔案描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 優化網路參數
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 擴展策略

#### 水平擴展

1. **多實例部署**
   ```bash
   # 啟動多個調度器實例
   python scheduler_api.py --port 8080 &
   python scheduler_api.py --port 8081 &
   python scheduler_api.py --port 8082 &
   ```

2. **負載均衡配置**
   ```nginx
   upstream scheduler_backend {
       server localhost:8080;
       server localhost:8081;
       server localhost:8082;
   }
   
   server {
       listen 80;
       location / {
           proxy_pass http://scheduler_backend;
       }
   }
   ```

#### 垂直擴展

1. **增加資源配置**
   ```json
   {
     "processing": {
       "max_workers": 20,        // 增加工作線程
       "batch_size": 100         // 增加批處理大小
     }
   }
   ```

2. **Redis集群**
   ```bash
   # 配置Redis集群
   redis-cli --cluster create \
     127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
     127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
     --cluster-replicas 1
   ```

## 安全配置

### 網路安全

#### 防火牆配置
```bash
# Ubuntu/Debian
sudo ufw allow 8080/tcp
sudo ufw allow 6379/tcp  # 僅內部網路
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --reload
```

#### SSL/TLS配置
```json
{
  "api": {
    "ssl_enabled": true,
    "ssl_cert_file": "/path/to/cert.pem",
    "ssl_key_file": "/path/to/key.pem"
  }
}
```

### 認證授權

#### API金鑰認證
```json
{
  "security": {
    "api_key_enabled": true,
    "api_keys": {
      "admin": "your-admin-api-key",
      "readonly": "your-readonly-api-key"
    }
  }
}
```

#### JWT認證
```json
{
  "security": {
    "jwt_enabled": true,
    "jwt_secret": "your-jwt-secret",
    "jwt_expiration": 3600
  }
}
```

### 數據安全

#### 檔案權限
```bash
# 設置適當的檔案權限
chmod 750 data/
chmod 640 scheduler_config.json
chown -R scheduler:scheduler data/
```

#### 敏感數據加密
```json
{
  "security": {
    "encryption_enabled": true,
    "encryption_key": "your-encryption-key",
    "encrypt_sensitive_fields": ["api_keys", "passwords"]
  }
}
```

## 監控和警報

### Prometheus集成

#### 配置Prometheus指標
```python
# 在scheduler_api.py中添加
from prometheus_client import Counter, Histogram, Gauge, generate_latest

task_counter = Counter('scheduler_tasks_total', 'Total tasks processed')
task_duration = Histogram('scheduler_task_duration_seconds', 'Task processing duration')
queue_size = Gauge('scheduler_queue_size', 'Current queue size')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Prometheus配置
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'scheduler'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana儀表板

#### 關鍵指標面板
1. **系統概覽**
   - CPU使用率
   - 記憶體使用率
   - 磁碟使用率
   - 網路流量

2. **任務處理**
   - 任務處理速率
   - 任務成功率
   - 任務錯誤率
   - 平均處理時間

3. **隊列狀態**
   - 隊列大小
   - 等待時間
   - 工作線程使用率

4. **Redis指標**
   - 連接數
   - 記憶體使用
   - 命令執行率

### 警報規則

#### Prometheus警報
```yaml
# alerts.yml
groups:
  - name: scheduler
    rules:
      - alert: HighCPUUsage
        expr: scheduler_cpu_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Scheduler CPU usage is high"
          
      - alert: HighQueueSize
        expr: scheduler_queue_size > 1000
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Scheduler queue size is too large"
```

## 災難恢復

### 備份策略

#### 自動備份腳本
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/scheduler"
DATE=$(date +%Y%m%d_%H%M%S)

# 創建備份目錄
mkdir -p $BACKUP_DIR/$DATE

# 備份配置檔案
cp scheduler_config.json $BACKUP_DIR/$DATE/

# 備份數據目錄
tar -czf $BACKUP_DIR/$DATE/data.tar.gz data/

# 備份Redis數據
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/$DATE/

# 清理舊備份（保留30天）
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

#### 定時備份
```bash
# 添加到crontab
crontab -e

# 每天凌晨2點備份
0 2 * * * /path/to/backup.sh

# 每小時備份Redis
0 * * * * redis-cli BGSAVE
```

### 恢復程序

#### 完整系統恢復
```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/backup/scheduler/$BACKUP_DATE"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# 停止服務
pkill -f scheduler_api.py
sudo systemctl stop redis

# 恢復配置
cp $BACKUP_DIR/scheduler_config.json .

# 恢復數據
tar -xzf $BACKUP_DIR/data.tar.gz

# 恢復Redis數據
sudo cp $BACKUP_DIR/dump.rdb /var/lib/redis/
sudo chown redis:redis /var/lib/redis/dump.rdb

# 重啟服務
sudo systemctl start redis
python scheduler_api.py &

echo "Restore completed from: $BACKUP_DIR"
```

### 高可用性配置

#### 主從複製
```bash
# 主節點Redis配置
echo "bind 0.0.0.0" >> /etc/redis/redis.conf
echo "requirepass your-password" >> /etc/redis/redis.conf

# 從節點Redis配置
echo "replicaof master-ip 6379" >> /etc/redis/redis.conf
echo "masterauth your-password" >> /etc/redis/redis.conf
```

#### 故障轉移
```python
# 在scheduler中實現Redis故障轉移
import redis.sentinel

sentinel = redis.sentinel.Sentinel([
    ('sentinel1', 26379),
    ('sentinel2', 26379),
    ('sentinel3', 26379)
])

master = sentinel.master_for('mymaster', socket_timeout=0.1)
slave = sentinel.slave_for('mymaster', socket_timeout=0.1)
```

## 最佳實踐

### 開發環境

1. **使用虛擬環境**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **配置開發模式**
   ```json
   {
     "deployment": {
       "environment": "development",
       "debug_mode": true,
       "auto_reload": true
     }
   }
   ```

3. **使用測試數據**
   ```bash
   # 生成測試JSON檔案
   python -c "
   import json
   import uuid
   from datetime import datetime
   
   test_data = {
       'id': str(uuid.uuid4()),
       'timestamp': datetime.now().isoformat(),
       'content': 'test job search query',
       'metadata': {'source': 'test', 'priority': 'low'}
   }
   
   with open('data/llm_generated/raw/test.json', 'w') as f:
       json.dump(test_data, f)
   "
   ```

### 生產環境

1. **資源監控**
   - 設置CPU、記憶體、磁碟使用警報
   - 監控網路延遲和吞吐量
   - 追蹤應用程式性能指標

2. **日誌管理**
   - 使用結構化日誌格式
   - 實施日誌輪轉和歸檔
   - 集中化日誌收集和分析

3. **安全加固**
   - 定期更新依賴套件
   - 實施最小權限原則
   - 啟用審計日誌

4. **性能調優**
   - 定期進行性能測試
   - 優化數據庫查詢
   - 實施緩存策略

### 運維自動化

1. **CI/CD流水線**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy Scheduler
   on:
     push:
       branches: [main]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Deploy to production
           run: |
             ssh user@server 'cd /app && git pull && python deploy_scheduler.py deploy'
   ```

2. **健康檢查**
   ```bash
   #!/bin/bash
   # health_check.sh
   
   # 檢查API健康狀態
   if ! curl -f http://localhost:8080/health; then
       echo "API health check failed, restarting..."
       python monitor_scheduler.py restart
   fi
   
   # 檢查Redis連接
   if ! redis-cli ping; then
       echo "Redis connection failed, restarting..."
       sudo systemctl restart redis
   fi
   ```

3. **自動擴展**
   ```python
   # auto_scale.py
   import psutil
   import subprocess
   
   def check_and_scale():
       cpu_usage = psutil.cpu_percent(interval=60)
       memory_usage = psutil.virtual_memory().percent
       
       if cpu_usage > 80 or memory_usage > 85:
           # 啟動額外的工作進程
           subprocess.run(['python', 'scheduler_api.py', '--port', '8081'])
           
       elif cpu_usage < 30 and memory_usage < 50:
           # 停止多餘的工作進程
           subprocess.run(['pkill', '-f', 'scheduler_api.py.*8081'])
   ```

## 故障排除指南

### 常見錯誤和解決方案

#### 1. 連接錯誤

**問題**: `ConnectionRefusedError: [Errno 111] Connection refused`

**原因**: Redis服務未啟動或配置錯誤

**解決方案**:
```bash
# 檢查Redis狀態
sudo systemctl status redis

# 啟動Redis
sudo systemctl start redis

# 檢查配置
redis-cli ping
```

#### 2. 記憶體不足

**問題**: `MemoryError: Unable to allocate memory`

**原因**: 系統記憶體不足或記憶體洩漏

**解決方案**:
```bash
# 檢查記憶體使用
free -h
ps aux --sort=-%mem | head

# 重啟服務釋放記憶體
python monitor_scheduler.py restart

# 調整工作線程數
# 在配置中減少max_workers
```

#### 3. 檔案權限錯誤

**問題**: `PermissionError: [Errno 13] Permission denied`

**原因**: 檔案或目錄權限不正確

**解決方案**:
```bash
# 檢查權限
ls -la data/

# 修正權限
chmod -R 755 data/
chown -R $USER:$USER data/
```

#### 4. 端口占用

**問題**: `OSError: [Errno 98] Address already in use`

**原因**: 指定端口已被其他進程使用

**解決方案**:
```bash
# 查找占用端口的進程
netstat -tulpn | grep 8080
lsof -i :8080

# 終止進程或更改端口
kill -9 <PID>
# 或在配置中更改端口
```

### 性能問題診斷

#### 1. 任務處理緩慢

**診斷步驟**:
```bash
# 檢查系統資源
top
iotop

# 檢查隊列積壓
redis-cli LLEN scheduler:queue:high

# 分析處理時間
grep "Processing time" logs/scheduler.log | tail -100
```

**優化建議**:
- 增加工作線程數
- 優化任務處理邏輯
- 使用更快的儲存設備

#### 2. 記憶體使用過高

**診斷步驟**:
```bash
# 檢查進程記憶體使用
ps aux --sort=-%mem

# 使用記憶體分析工具
python -m memory_profiler scheduler_api.py
```

**優化建議**:
- 實施記憶體池
- 優化數據結構
- 增加垃圾回收頻率

## 版本升級

### 升級前準備

1. **備份當前系統**
   ```bash
   ./backup.sh
   ```

2. **測試新版本**
   ```bash
   # 在測試環境中部署新版本
   git checkout new-version
   python deploy_scheduler.py deploy --method local
   ```

3. **檢查相容性**
   - 檢查配置檔案格式變更
   - 驗證API介面相容性
   - 測試數據遷移腳本

### 升級步驟

1. **停止服務**
   ```bash
   python monitor_scheduler.py restart
   ```

2. **更新代碼**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

3. **遷移數據**
   ```bash
   # 如果需要數據遷移
   python migrate_data.py --from-version 1.0 --to-version 2.0
   ```

4. **更新配置**
   ```bash
   # 合併新的配置選項
   python update_config.py
   ```

5. **重啟服務**
   ```bash
   python scheduler_api.py
   ```

6. **驗證升級**
   ```bash
   python monitor_scheduler.py status
   ```

### 回滾程序

如果升級失敗，可以快速回滾：

```bash
#!/bin/bash
# rollback.sh

BACKUP_DATE=$1

echo "Rolling back to $BACKUP_DATE..."

# 停止服務
pkill -f scheduler_api.py

# 恢復代碼
git checkout previous-version

# 恢復數據和配置
./restore.sh $BACKUP_DATE

# 重啟服務
python scheduler_api.py &

echo "Rollback completed"
```

## 支援和社群

### 技術支援

- **文檔**: 查看完整的API文檔和使用指南
- **問題追蹤**: 在GitHub Issues中報告問題
- **討論區**: 參與社群討論和經驗分享

### 貢獻指南

1. **代碼貢獻**
   - Fork專案倉庫
   - 創建功能分支
   - 提交Pull Request

2. **文檔改進**
   - 修正文檔錯誤
   - 添加使用範例
   - 翻譯文檔

3. **測試和回饋**
   - 報告Bug
   - 建議新功能
   - 分享使用經驗

### 版本發布

- **穩定版本**: 每季度發布，包含新功能和Bug修復
- **補丁版本**: 每月發布，主要修復安全問題和關鍵Bug
- **開發版本**: 持續集成，包含最新功能（不建議生產使用）

---

**注意**: 本指南會隨著系統更新而持續改進。建議定期查看最新版本的部署指南。

如有任何問題或建議，請聯繫技術支援團隊或在社群中提出討論。