#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy Windows Production Server
使用內建 werkzeug 伺服器的生產優化版本

Author: Jason Yu (jason660519)
Date: 2025-01-04
"""

import os
import sys
import threading
import time
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_production_environment():
    """設置生產環境"""
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    
def start_production_server(host='0.0.0.0', port=5000, threaded=True, processes=1):
    """
    啟動生產級 Flask 伺服器
    
    使用 werkzeug 伺服器的生產優化配置，適用於 Windows 環境
    """
    setup_production_environment()
    
    print("🚀 JobSpy 生產伺服器啟動中...")
    print(f"📱 本地訪問: http://localhost:{port}")
    print(f"📱 網路訪問: http://192.168.1.181:{port}")
    print(f"🔧 監聽地址: {host}:{port}")
    print(f"🧵 多線程: {'啟用' if threaded else '停用'}")
    print(f"⚙️ 環境: 生產模式")
    print("\n按 Ctrl+C 停止伺服器\n")
    
    try:
        from app import app
        
        # 生產環境配置
        app.config.update(
            DEBUG=False,
            TESTING=False,
            SECRET_KEY=os.environ.get('SECRET_KEY', 'jobseeker-production-key-2025'),
            # 安全標頭
            SESSION_COOKIE_SECURE=False,  # 在 HTTPS 環境中設為 True
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            # 效能設定
            SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1年
        )
        
        # 啟動伺服器
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=threaded,
            processes=processes,
            use_reloader=False,
            use_debugger=False,
            use_evalex=False,
            # 增加請求處理能力
            request_handler=None,
            ssl_context=None
        )
        
    except KeyboardInterrupt:
        print("\n👋 生產伺服器已停止")
    except Exception as e:
        print(f"❌ 伺服器啟動失敗: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JobSpy Windows 生產伺服器')
    parser.add_argument('--host', default='0.0.0.0', help='監聽地址')
    parser.add_argument('--port', type=int, default=5000, help='監聽端口')
    parser.add_argument('--no-threading', action='store_true', help='停用多線程')
    
    args = parser.parse_args()
    
    start_production_server(
        host=args.host,
        port=args.port,
        threaded=not args.no_threading
    )