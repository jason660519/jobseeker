#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 網頁應用啟動腳本

這個腳本提供了多種啟動模式：
1. 開發模式 - 啟用除錯和自動重載
2. 生產模式 - 使用 Gunicorn WSGI 伺服器
3. Docker 模式 - 容器化部署

使用方法:
    python run.py --mode dev     # 開發模式
    python run.py --mode prod    # 生產模式
    python run.py --help         # 顯示幫助

Author: jobseeker Team
Date: 2025-01-27
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """
    檢查必要的依賴套件是否已安裝
    """
    required_packages = [
        'flask',
        'flask_cors',
        'pandas',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少必要的依賴套件:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n請執行以下命令安裝依賴:")
        print(f"   pip install -r {Path(__file__).parent / 'requirements.txt'}")
        return False
    
    return True

def check_jobseeker_installation():
    """
    檢查 jobseeker 套件是否已正確安裝
    """
    try:
        from jobseeker.route_manager import smart_scrape_jobs
        from jobseeker.model import Site, Country
        print("✅ jobseeker 套件已正確安裝")
        return True
    except ImportError as e:
        print(f"❌ jobseeker 套件未正確安裝: {e}")
        print("\n請執行以下命令安裝 jobseeker:")
        print(f"   cd {project_root}")
        print("   pip install -e .")
        return False

def run_development_server(host='0.0.0.0', port=5000, debug=True):
    """
    啟動開發伺服器
    
    Args:
        host: 伺服器主機地址
        port: 伺服器端口
        debug: 是否啟用除錯模式
    """
    print("🚀 啟動開發伺服器...")
    print(f"📱 訪問地址: http://{host}:{port}")
    print(f"🔧 除錯模式: {'啟用' if debug else '停用'}")
    print("\n按 Ctrl+C 停止伺服器\n")
    
    # 設置環境變數
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = str(debug).lower()
    
    # 導入並啟動應用
    from app import app
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

def run_production_server(host='0.0.0.0', port=5000, workers=4):
    """
    使用 Gunicorn 啟動生產伺服器
    
    Args:
        host: 伺服器主機地址
        port: 伺服器端口
        workers: 工作進程數量
    """
    print("🚀 啟動生產伺服器 (Gunicorn)...")
    print(f"📱 訪問地址: http://{host}:{port}")
    print(f"👥 工作進程: {workers}")
    print("\n按 Ctrl+C 停止伺服器\n")
    
    # 設置環境變數
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    
    # 檢查 Gunicorn 是否已安裝
    try:
        import gunicorn
    except ImportError:
        print("❌ Gunicorn 未安裝，請執行: pip install gunicorn")
        return
    
    # 啟動 Gunicorn
    cmd = [
        'gunicorn',
        '--bind', f'{host}:{port}',
        '--workers', str(workers),
        '--worker-class', 'sync',
        '--timeout', '120',
        '--keep-alive', '5',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--access-logfile', '-',
        '--error-logfile', '-',
        'app:app'
    ]
    
    try:
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n👋 伺服器已停止")

def create_docker_files():
    """
    創建 Docker 相關檔案
    """
    web_app_dir = Path(__file__).parent
    
    # Dockerfile
    dockerfile_content = '''
# jobseeker 網頁應用 Dockerfile
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 複製 jobseeker 套件
COPY ../jobseeker /app/jobseeker
COPY ../setup.py /app/
COPY ../README.md /app/

# 安裝 jobseeker 套件
RUN pip install -e .

# 暴露端口
EXPOSE 5000

# 啟動命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
'''
    
    with open(web_app_dir / 'Dockerfile', 'w', encoding='utf-8') as f:
        f.write(dockerfile_content.strip())
    
    # docker-compose.yml
    compose_content = '''
version: '3.8'

services:
  jobseeker-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=false
    volumes:
      - ./downloads:/app/downloads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
    
    with open(web_app_dir / 'docker-compose.yml', 'w', encoding='utf-8') as f:
        f.write(compose_content.strip())
    
    print("✅ Docker 檔案已創建:")
    print(f"   - {web_app_dir / 'Dockerfile'}")
    print(f"   - {web_app_dir / 'docker-compose.yml'}")
    print("\n使用 Docker 啟動:")
    print("   docker-compose up --build")

def main():
    """
    主函數
    """
    parser = argparse.ArgumentParser(
        description='jobseeker 網頁應用啟動腳本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例:
  python run.py --mode dev                    # 開發模式
  python run.py --mode prod --workers 8      # 生產模式，8個工作進程
  python run.py --mode dev --port 8080       # 開發模式，使用端口 8080
  python run.py --create-docker              # 創建 Docker 檔案
        '''
    )
    
    parser.add_argument(
        '--mode',
        choices=['dev', 'prod'],
        default='dev',
        help='啟動模式 (預設: dev)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='伺服器主機地址 (預設: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='伺服器端口 (預設: 5000)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='生產模式工作進程數量 (預設: 4)'
    )
    
    parser.add_argument(
        '--no-debug',
        action='store_true',
        help='開發模式下停用除錯'
    )
    
    parser.add_argument(
        '--create-docker',
        action='store_true',
        help='創建 Docker 相關檔案'
    )
    
    args = parser.parse_args()
    
    # 創建 Docker 檔案
    if args.create_docker:
        create_docker_files()
        return
    
    print("🔍 檢查環境...")
    
    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)
    
    # 檢查 jobseeker 安裝
    if not check_jobseeker_installation():
        sys.exit(1)
    
    # 創建下載目錄
    downloads_dir = Path(__file__).parent / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    
    print("✅ 環境檢查完成\n")
    
    # 啟動伺服器
    try:
        if args.mode == 'dev':
            run_development_server(
                host=args.host,
                port=args.port,
                debug=not args.no_debug
            )
        elif args.mode == 'prod':
            run_production_server(
                host=args.host,
                port=args.port,
                workers=args.workers
            )
    except KeyboardInterrupt:
        print("\n👋 伺服器已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()