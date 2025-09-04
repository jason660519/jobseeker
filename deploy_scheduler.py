#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON調度器部署腳本
用於快速部署和管理調度器系統

Author: JobSpy Team
Date: 2025-01-27
"""

import os
import sys
import json
import time
import asyncio
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import yaml

# 導入必要的模組
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    print("警告: Docker Python客戶端未安裝，Docker功能將不可用")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil未安裝，系統監控功能將受限")


class SchedulerDeployer:
    """
    調度器部署管理器
    負責部署、配置和管理調度器系統
    """

    def __init__(self, config_file: str = "scheduler_config.json"):
        self.config_file = Path(config_file)
        self.project_root = Path.cwd()
        self.config = self._load_config()
        
        # 部署相關路徑
        self.deploy_dir = self.project_root / "deployment"
        self.logs_dir = self.project_root / "logs"
        self.data_dir = self.project_root / "data"
        
        # Docker相關
        self.docker_client = None
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                print(f"Docker連接失敗: {e}")

    def _load_config(self) -> Dict:
        """載入配置檔案"""
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"配置檔案不存在: {self.config_file}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """獲取預設配置"""
        
        return {
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
            },
            "deployment": {
                "environment": "development",
                "debug_mode": True
            }
        }

    def setup_directories(self):
        """設置必要的目錄結構"""
        
        print("正在設置目錄結構...")
        
        # 創建基本目錄
        directories = [
            self.deploy_dir,
            self.logs_dir,
            self.data_dir,
            self.data_dir / "llm_generated" / "raw",
            self.data_dir / "llm_generated" / "processed",
            self.data_dir / "llm_generated" / "archive",
            self.data_dir / "llm_generated" / "errors",
            self.data_dir / "llm_generated" / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ 創建目錄: {directory}")
        
        # 設置權限（Unix系統）
        if os.name != 'nt':  # 非Windows系統
            for directory in directories:
                os.chmod(directory, 0o755)
        
        print("目錄結構設置完成")

    def install_dependencies(self):
        """安裝Python依賴"""
        
        print("正在安裝Python依賴...")
        
        # 基本依賴列表
        dependencies = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "redis>=5.0.0",
            "aioredis>=2.0.0",
            "aiofiles>=23.0.0",
            "watchdog>=3.0.0",
            "psutil>=5.9.0",
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6",
            "docker>=6.0.0"
        ]
        
        # 檢查是否在虛擬環境中
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if not in_venv:
            print("警告: 建議在虛擬環境中安裝依賴")
            response = input("是否繼續安裝? (y/N): ")
            if response.lower() != 'y':
                print("安裝已取消")
                return False
        
        try:
            for dep in dependencies:
                print(f"  正在安裝: {dep}")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"  ✓ 已安裝: {dep}")
            
            print("所有依賴安裝完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"依賴安裝失敗: {e}")
            return False

    def setup_redis(self, method: str = "docker"):
        """設置Redis服務"""
        
        print(f"正在設置Redis服務 (方法: {method})...")
        
        if method == "docker" and self.docker_client:
            return self._setup_redis_docker()
        elif method == "local":
            return self._setup_redis_local()
        else:
            print("無效的Redis設置方法或Docker不可用")
            return False

    def _setup_redis_docker(self) -> bool:
        """使用Docker設置Redis"""
        
        try:
            # 檢查是否已有Redis容器
            containers = self.docker_client.containers.list(all=True, filters={"name": "scheduler-redis"})
            
            if containers:
                container = containers[0]
                if container.status != "running":
                    print("  啟動現有Redis容器...")
                    container.start()
                else:
                    print("  Redis容器已在運行")
            else:
                print("  創建新的Redis容器...")
                container = self.docker_client.containers.run(
                    "redis:7-alpine",
                    name="scheduler-redis",
                    ports={'6379/tcp': 6379},
                    detach=True,
                    restart_policy={"Name": "unless-stopped"}
                )
            
            # 等待Redis啟動
            print("  等待Redis啟動...")
            time.sleep(3)
            
            # 測試連接
            if self._test_redis_connection():
                print("  ✓ Redis設置成功")
                return True
            else:
                print("  ✗ Redis連接測試失敗")
                return False
                
        except Exception as e:
            print(f"  ✗ Redis Docker設置失敗: {e}")
            return False

    def _setup_redis_local(self) -> bool:
        """本地安裝Redis指導"""
        
        print("  本地Redis安裝指導:")
        print("  ") 
        print("  Windows:")
        print("    1. 下載Redis for Windows")
        print("    2. 解壓並運行redis-server.exe")
        print("  ")
        print("  Linux (Ubuntu/Debian):")
        print("    sudo apt update")
        print("    sudo apt install redis-server")
        print("    sudo systemctl start redis")
        print("  ")
        print("  macOS:")
        print("    brew install redis")
        print("    brew services start redis")
        print("  ")
        
        # 測試連接
        if self._test_redis_connection():
            print("  ✓ Redis連接成功")
            return True
        else:
            print("  ✗ Redis連接失敗，請確保Redis服務正在運行")
            return False

    def _test_redis_connection(self) -> bool:
        """測試Redis連接"""
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except Exception:
            return False

    def create_docker_compose(self):
        """創建Docker Compose配置"""
        
        print("正在創建Docker Compose配置...")
        
        compose_config = {
            'version': '3.8',
            'services': {
                'redis': {
                    'image': 'redis:7-alpine',
                    'container_name': 'scheduler-redis',
                    'ports': ['6379:6379'],
                    'restart': 'unless-stopped',
                    'volumes': ['redis_data:/data']
                },
                'scheduler': {
                    'build': {
                        'context': '.',
                        'dockerfile': 'Dockerfile'
                    },
                    'container_name': 'llm-scheduler',
                    'ports': ['8080:8080'],
                    'depends_on': ['redis'],
                    'environment': {
                        'REDIS_URL': 'redis://redis:6379/0',
                        'PYTHONPATH': '/app'
                    },
                    'volumes': [
                        './data:/app/data',
                        './logs:/app/logs',
                        './scheduler_config.json:/app/scheduler_config.json'
                    ],
                    'restart': 'unless-stopped'
                }
            },
            'volumes': {
                'redis_data': {}
            }
        }
        
        compose_file = self.deploy_dir / "docker-compose.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        print(f"  ✓ Docker Compose配置已創建: {compose_file}")

    def create_dockerfile(self):
        """創建Dockerfile"""
        
        print("正在創建Dockerfile...")
        
        dockerfile_content = '''
# 使用Python 3.11作為基礎鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建必要的目錄
RUN mkdir -p /app/data/llm_generated/{raw,processed,archive,errors,temp} \
    && mkdir -p /app/logs

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 啟動命令
CMD ["python", "scheduler_api.py", "--host", "0.0.0.0", "--port", "8080"]
'''
        
        dockerfile_path = self.project_root / "Dockerfile"
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content.strip())
        
        print(f"  ✓ Dockerfile已創建: {dockerfile_path}")

    def create_requirements_file(self):
        """創建requirements.txt文件"""
        
        print("正在創建requirements.txt...")
        
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "redis>=5.0.0",
            "aioredis>=2.0.0",
            "aiofiles>=23.0.0",
            "watchdog>=3.0.0",
            "psutil>=5.9.0",
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6",
            "pyyaml>=6.0.0",
            "requests>=2.31.0"
        ]
        
        requirements_file = self.project_root / "requirements.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
        
        print(f"  ✓ requirements.txt已創建: {requirements_file}")

    def create_systemd_service(self):
        """創建systemd服務文件（Linux）"""
        
        if os.name == 'nt':
            print("Windows系統不支持systemd服務")
            return
        
        print("正在創建systemd服務文件...")
        
        service_content = f'''
[Unit]
Description=LLM JSON Scheduler
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=scheduler
Group=scheduler
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
ExecStart={sys.executable} scheduler_api.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
        
        service_file = self.deploy_dir / "llm-scheduler.service"
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(service_content.strip())
        
        print(f"  ✓ systemd服務文件已創建: {service_file}")
        print("  ")
        print("  安裝服務的命令:")
        print(f"    sudo cp {service_file} /etc/systemd/system/")
        print("    sudo systemctl daemon-reload")
        print("    sudo systemctl enable llm-scheduler")
        print("    sudo systemctl start llm-scheduler")

    def create_startup_script(self):
        """創建啟動腳本"""
        
        print("正在創建啟動腳本...")
        
        # Windows批處理腳本
        if os.name == 'nt':
            script_content = f'''
@echo off
echo Starting LLM JSON Scheduler...

cd /d "{self.project_root}"

REM 檢查Python環境
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

REM 啟動調度器API
echo Starting Scheduler API...
python scheduler_api.py --host 0.0.0.0 --port 8080

pause
'''
            script_file = self.deploy_dir / "start_scheduler.bat"
        else:
            # Unix shell腳本
            script_content = f'''
#!/bin/bash

echo "Starting LLM JSON Scheduler..."

cd "{self.project_root}"

# 檢查Python環境
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 not found"
    exit 1
fi

# 檢查Redis連接
if ! python3 -c "import redis; redis.Redis().ping()" 2>/dev/null; then
    echo "Warning: Redis connection failed"
fi

# 啟動調度器API
echo "Starting Scheduler API..."
python3 scheduler_api.py --host 0.0.0.0 --port 8080
'''
            script_file = self.deploy_dir / "start_scheduler.sh"
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content.strip())
        
        # 設置執行權限（Unix系統）
        if os.name != 'nt':
            os.chmod(script_file, 0o755)
        
        print(f"  ✓ 啟動腳本已創建: {script_file}")

    def check_system_requirements(self) -> bool:
        """檢查系統需求"""
        
        print("正在檢查系統需求...")
        
        requirements_met = True
        
        # 檢查Python版本
        python_version = sys.version_info
        if python_version < (3, 8):
            print(f"  ✗ Python版本過低: {python_version.major}.{python_version.minor} (需要 >= 3.8)")
            requirements_met = False
        else:
            print(f"  ✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 檢查可用記憶體
        if PSUTIL_AVAILABLE:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            if available_gb < 1:
                print(f"  ⚠ 可用記憶體較低: {available_gb:.1f}GB")
            else:
                print(f"  ✓ 可用記憶體: {available_gb:.1f}GB")
        
        # 檢查磁碟空間
        if PSUTIL_AVAILABLE:
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024**3)
            if free_gb < 5:
                print(f"  ⚠ 可用磁碟空間較低: {free_gb:.1f}GB")
            else:
                print(f"  ✓ 可用磁碟空間: {free_gb:.1f}GB")
        
        # 檢查網路端口
        if PSUTIL_AVAILABLE:
            api_port = self.config.get("api", {}).get("port", 8080)
            connections = psutil.net_connections()
            port_in_use = any(conn.laddr.port == api_port for conn in connections if conn.laddr)
            
            if port_in_use:
                print(f"  ⚠ 端口 {api_port} 已被使用")
            else:
                print(f"  ✓ 端口 {api_port} 可用")
        
        return requirements_met

    def deploy(self, method: str = "local", redis_method: str = "docker"):
        """執行完整部署"""
        
        print("=" * 60)
        print("LLM JSON調度器部署開始")
        print("=" * 60)
        
        # 檢查系統需求
        if not self.check_system_requirements():
            print("\n系統需求檢查失敗，請解決問題後重試")
            return False
        
        print("\n" + "="*40)
        print("步驟 1: 設置目錄結構")
        print("="*40)
        self.setup_directories()
        
        print("\n" + "="*40)
        print("步驟 2: 安裝依賴")
        print("="*40)
        if not self.install_dependencies():
            print("依賴安裝失敗")
            return False
        
        print("\n" + "="*40)
        print("步驟 3: 設置Redis")
        print("="*40)
        if not self.setup_redis(redis_method):
            print("Redis設置失敗")
            return False
        
        print("\n" + "="*40)
        print("步驟 4: 創建部署文件")
        print("="*40)
        self.create_requirements_file()
        self.create_startup_script()
        
        if method == "docker":
            self.create_dockerfile()
            self.create_docker_compose()
        elif method == "systemd":
            self.create_systemd_service()
        
        print("\n" + "="*60)
        print("部署完成！")
        print("="*60)
        
        self._print_next_steps(method)
        
        return True

    def _print_next_steps(self, method: str):
        """打印後續步驟"""
        
        print("\n後續步驟:")
        print("-" * 30)
        
        if method == "local":
            print("1. 啟動調度器:")
            if os.name == 'nt':
                print(f"   {self.deploy_dir / 'start_scheduler.bat'}")
            else:
                print(f"   {self.deploy_dir / 'start_scheduler.sh'}")
            
            print("\n2. 或者手動啟動:")
            print("   python scheduler_api.py")
        
        elif method == "docker":
            print("1. 構建並啟動Docker容器:")
            print(f"   cd {self.deploy_dir}")
            print("   docker-compose up -d")
            
            print("\n2. 查看日誌:")
            print("   docker-compose logs -f")
        
        elif method == "systemd":
            print("1. 安裝systemd服務:")
            print(f"   sudo cp {self.deploy_dir}/llm-scheduler.service /etc/systemd/system/")
            print("   sudo systemctl daemon-reload")
            print("   sudo systemctl enable llm-scheduler")
            print("   sudo systemctl start llm-scheduler")
        
        print("\n3. 訪問API文檔:")
        api_port = self.config.get("api", {}).get("port", 8080)
        print(f"   http://localhost:{api_port}/docs")
        
        print("\n4. 健康檢查:")
        print(f"   http://localhost:{api_port}/health")

    def status(self):
        """檢查調度器狀態"""
        
        print("調度器狀態檢查")
        print("=" * 40)
        
        # 檢查API服務
        api_port = self.config.get("api", {}).get("port", 8080)
        
        try:
            import requests
            response = requests.get(f"http://localhost:{api_port}/health", timeout=5)
            if response.status_code == 200:
                print(f"  ✓ API服務運行正常 (端口 {api_port})")
                
                # 獲取詳細狀態
                status_response = requests.get(f"http://localhost:{api_port}/status", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"  ✓ 已處理任務: {status_data.get('scheduler_stats', {}).get('total_files_processed', 0)}")
                    print(f"  ✓ 活躍工作線程: {status_data.get('worker_stats', {}).get('active_workers', 0)}")
            else:
                print(f"  ✗ API服務響應異常 (狀態碼: {response.status_code})")
        except Exception as e:
            print(f"  ✗ API服務無法訪問: {e}")
        
        # 檢查Redis
        if self._test_redis_connection():
            print("  ✓ Redis服務運行正常")
        else:
            print("  ✗ Redis服務無法連接")
        
        # 檢查目錄
        watch_dir = Path(self.config.get("directories", {}).get("watch_directory", "./data/llm_generated/raw"))
        if watch_dir.exists():
            file_count = len(list(watch_dir.glob("*.json")))
            print(f"  ✓ 監控目錄存在，包含 {file_count} 個JSON檔案")
        else:
            print(f"  ✗ 監控目錄不存在: {watch_dir}")


def main():
    """主程序入口"""
    
    parser = argparse.ArgumentParser(description="LLM JSON調度器部署工具")
    parser.add_argument("action", choices=["deploy", "status", "setup-dirs", "install-deps", "setup-redis"],
                       help="要執行的操作")
    parser.add_argument("--method", choices=["local", "docker", "systemd"], default="local",
                       help="部署方法")
    parser.add_argument("--redis-method", choices=["docker", "local"], default="docker",
                       help="Redis設置方法")
    parser.add_argument("--config", default="scheduler_config.json",
                       help="配置檔案路徑")
    
    args = parser.parse_args()
    
    deployer = SchedulerDeployer(args.config)
    
    if args.action == "deploy":
        success = deployer.deploy(args.method, args.redis_method)
        sys.exit(0 if success else 1)
    
    elif args.action == "status":
        deployer.status()
    
    elif args.action == "setup-dirs":
        deployer.setup_directories()
    
    elif args.action == "install-deps":
        success = deployer.install_dependencies()
        sys.exit(0 if success else 1)
    
    elif args.action == "setup-redis":
        success = deployer.setup_redis(args.redis_method)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()