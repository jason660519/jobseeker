#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 網頁應用生產環境啟動腳本（Windows 相容版）

這個腳本使用 Waitress WSGI 伺服器，完全相容 Windows 環境，
提供生產級別的效能和穩定性。

使用方法:
    python run_production.py                    # 使用預設設定
    python run_production.py --port 8080        # 自定義端口
    python run_production.py --workers 8        # 自定義線程數

Author: Jason Yu (jason660519)
Date: 2025-01-04
"""

import os
import sys
import argparse
import signal
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_production_environment():
    """設置生產環境變數"""
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    os.environ['PYTHONUNBUFFERED'] = '1'
    
def check_dependencies():
    """檢查必要的依賴套件"""
    print("🔍 檢查生產環境依賴...")
    
    required_packages = ['waitress', 'flask']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少必要的套件:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n請執行: pip install waitress")
        return False
    
    print("✅ 依賴檢查完成")
    return True

def start_production_server(host='0.0.0.0', port=5000, threads=6, cleanup_interval=30):
    """
    使用 Waitress 啟動生產伺服器
    
    Args:
        host: 監聽地址
        port: 監聽端口
        threads: 線程數
        cleanup_interval: 清理間隔（秒）
    """
    if not check_dependencies():
        return
    
    setup_production_environment()
    
    print("🚀 啟動 JobSpy 生產伺服器...")
    print(f"📱 本地訪問: http://localhost:{port}")
    print(f"📱 網路訪問: http://192.168.1.181:{port}")
    print(f"🔧 監聽地址: {host}:{port}")
    print(f"🧵 線程數: {threads}")
    print(f"🔄 清理間隔: {cleanup_interval}s")
    print("\n按 Ctrl+C 停止伺服器\n")
    
    try:
        from waitress import serve
        from app import app
        
        # 配置 Waitress 伺服器
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            cleanup_interval=cleanup_interval,
            connection_limit=1000,
            channel_timeout=120,
            # 防止 DOS 攻擊
            send_bytes=18000,  # 18KB per send
            # 優化設定
            asyncore_use_poll=True,
            # 日誌設定
            ident='JobSpy-Waitress'
        )
        
    except KeyboardInterrupt:
        print("\n👋 伺服器已停止")
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請確保已安裝 waitress: pip install waitress")
    except Exception as e:
        print(f"❌ 伺服器啟動失敗: {e}")

def create_service_script():
    """創建 Windows 服務腳本"""
    service_script = '''
@echo off
echo 🚀 啟動 JobSpy 生產服務
cd /d "%~dp0"

REM 啟動虛擬環境
if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
) else if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
)

REM 啟動生產伺服器
python web_app\\run_production.py

pause
'''
    
    script_path = Path(__file__).parent.parent / 'start_production_server.bat'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(service_script.strip())
    
    print(f"✅ 已創建服務腳本: {script_path}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='JobSpy 生產環境伺服器（Windows 相容版）'
    )
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='監聽地址 (預設: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        help='監聽端口 (預設: 5000)'
    )
    parser.add_argument(
        '--threads', 
        type=int, 
        default=6,
        help='工作線程數 (預設: 6)'
    )
    parser.add_argument(
        '--cleanup-interval', 
        type=int, 
        default=30,
        help='清理間隔秒數 (預設: 30)'
    )
    parser.add_argument(
        '--create-service', 
        action='store_true',
        help='創建 Windows 服務腳本'
    )
    
    args = parser.parse_args()
    
    if args.create_service:
        create_service_script()
        return
    
    start_production_server(
        host=args.host,
        port=args.port,
        threads=args.threads,
        cleanup_interval=args.cleanup_interval
    )

if __name__ == '__main__':
    main()