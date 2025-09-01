# jobseeker Dockerfile
# 多階段建置，支援開發、測試和生產環境

# ==================== 基礎映像 ====================
FROM python:3.9-slim as base

# 設置環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 創建應用用戶
RUN groupadd -r jobseeker && useradd -r -g jobseeker jobseeker

# 設置工作目錄
WORKDIR /app

# 複製需求檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==================== 開發環境 ====================
FROM base as development

# 安裝開發和測試依賴
COPY requirements-dev.txt requirements-test.txt ./
RUN pip install -r requirements-dev.txt && \
    pip install -r requirements-test.txt

# 安裝額外的開發工具
RUN pip install \
    jupyter \
    ipython \
    notebook \
    jupyterlab

# 複製專案檔案
COPY . .

# 設置權限
RUN chown -R jobseeker:jobseeker /app

# 切換到應用用戶
USER jobseeker

# 暴露端口（用於 Jupyter 等）
EXPOSE 8888 8000

# 預設命令
CMD ["python", "-c", "print('jobseeker 開發環境已準備就緒！'); import jobseeker; print(f'jobseeker 版本: {jobseeker.__version__ if hasattr(jobseeker, \"__version__\") else \"開發版\"}')"]

# ==================== 測試環境 ====================
FROM base as testing

# 安裝測試依賴
COPY requirements-test.txt .
RUN pip install -r requirements-test.txt

# 複製專案檔案
COPY . .

# 設置測試環境變數
ENV jobseeker_TEST_ENV=ci \
    jobseeker_CACHE_ENABLED=false \
    jobseeker_MOCK_NETWORK=true \
    jobseeker_VERBOSE=false

# 設置權限
RUN chown -R jobseeker:jobseeker /app

# 切換到應用用戶
USER jobseeker

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import jobseeker; print('jobseeker 可正常導入')" || exit 1

# 預設執行測試
CMD ["python", "test_runner.py", "--all"]

# ==================== 生產環境 ====================
FROM base as production

# 只複製必要的檔案
COPY jobseeker/ ./jobseeker/
COPY setup.py README.md LICENSE ./

# 安裝套件
RUN pip install .

# 設置權限
RUN chown -R jobseeker:jobseeker /app

# 切換到應用用戶
USER jobseeker

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import jobseeker; print('jobseeker 運行正常')" || exit 1

# 預設命令
CMD ["python", "-c", "import jobseeker; print('jobseeker 生產環境已準備就緒！')"]

# ==================== 輕量級生產環境 ====================
FROM python:3.9-alpine as production-alpine

# 安裝系統依賴
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    curl

# 設置環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 創建應用用戶
RUN addgroup -g 1000 jobseeker && \
    adduser -D -s /bin/sh -u 1000 -G jobseeker jobseeker

# 設置工作目錄
WORKDIR /app

# 複製需求檔案並安裝依賴
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 複製應用程式碼
COPY jobseeker/ ./jobseeker/
COPY setup.py README.md ./

# 安裝套件
RUN pip install .

# 設置權限
RUN chown -R jobseeker:jobseeker /app

# 切換到應用用戶
USER jobseeker

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import jobseeker" || exit 1

# 預設命令
CMD ["python", "-c", "import jobseeker; print('jobseeker Alpine 版本運行正常！')"]

# ==================== 多架構支援 ====================
# 使用 buildx 建置多架構映像：
# docker buildx build --platform linux/amd64,linux/arm64 -t jobseeker:latest .

# ==================== 建置說明 ====================
# 
# 建置開發環境：
# docker build --target development -t jobseeker:dev .
# 
# 建置測試環境：
# docker build --target testing -t jobseeker:test .
# 
# 建置生產環境：
# docker build --target production -t jobseeker:prod .
# 
# 建置 Alpine 版本：
# docker build --target production-alpine -t jobseeker:alpine .
# 
# 執行範例：
# 
# 開發環境：
# docker run -it --rm -v $(pwd):/app -p 8888:8888 jobseeker:dev bash
# 
# 測試環境：
# docker run --rm jobseeker:test
# 
# 生產環境：
# docker run --rm jobseeker:prod
# 
# 互動式 Python：
# docker run -it --rm jobseeker:prod python
# 
# 執行特定腳本：
# docker run --rm -v $(pwd)/examples:/examples jobseeker:prod python /examples/basic_usage.py
# 
# Jupyter Notebook（開發環境）：
# docker run -it --rm -p 8888:8888 -v $(pwd):/app jobseeker:dev jupyter lab --ip=0.0.0.0 --allow-root
# 
# ==================== Docker Compose 支援 ====================
# 
# 可以配合 docker-compose.yml 使用：
# 
# version: '3.8'
# services:
#   jobseeker-dev:
#     build:
#       context: .
#       target: development
#     volumes:
#       - .:/app
#     ports:
#       - "8888:8888"
#       - "8000:8000"
#     environment:
#       - jobseeker_DEBUG=true
#   
#   jobseeker-test:
#     build:
#       context: .
#       target: testing
#     environment:
#       - jobseeker_TEST_ENV=ci
#   
#   jobseeker-prod:
#     build:
#       context: .
#       target: production
#     restart: unless-stopped
# 
# ==================== 安全性注意事項 ====================
# 
# 1. 使用非 root 用戶運行
# 2. 最小化映像大小
# 3. 定期更新基礎映像
# 4. 掃描安全漏洞：docker scan jobseeker:latest
# 5. 使用 .dockerignore 排除敏感檔案
# 
# ==================== 效能優化 ====================
# 
# 1. 使用多階段建置減少映像大小
# 2. 利用 Docker 層快取
# 3. 合併 RUN 指令減少層數
# 4. 使用 Alpine 基礎映像（生產環境）
# 5. 清理 apt/apk 快取
# 
# ==================== 監控和日誌 ====================
# 
# 健康檢查：
# docker inspect --format='{{.State.Health.Status}}' <container_id>
# 
# 查看日誌：
# docker logs <container_id>
# 
# 即時日誌：
# docker logs -f <container_id>
# 
# 進入容器：
# docker exec -it <container_id> bash
# 
# ==================== 標籤建議 ====================
# 
# 版本標籤：
# jobseeker:1.0.0
# jobseeker:1.0
# jobseeker:latest
# 
# 環境標籤：
# jobseeker:dev
# jobseeker:test
# jobseeker:prod
# jobseeker:alpine
# 
# 架構標籤：
# jobseeker:amd64
# jobseeker:arm64
# 
# 日期標籤：
# jobseeker:2024-01-15
# jobseeker:20240115
#