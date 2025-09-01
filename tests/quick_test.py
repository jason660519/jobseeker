#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 快速測試腳本

這個腳本提供最簡單的方式來測試 jobseeker 的所有9個網站功能。
支援的網站：LinkedIn, Indeed, ZipRecruiter, Glassdoor, Google, Bayt, Naukri, BDJobs, Seek

Author: jobseeker Team
Date: 2024
"""

import os
import sys
from pathlib import Path

# 設定路徑
project_root = Path(__file__).parent.parent
tests_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_dir))

def main():
    """
    主要測試執行函數
    """
    print("🚀 jobseeker 快速測試開始...")
    print("📍 支援的網站：LinkedIn, Indeed, ZipRecruiter, Glassdoor, Google, Bayt, Naukri, BDJobs, Seek")
    print("="*60)
    
    try:
        # 導入必要模組
        import pytest
        import subprocess
        
        # 切換到測試目錄
        os.chdir(tests_dir)
        
        print("\n1️⃣ 執行基本功能測試...")
        result1 = subprocess.run([
            sys.executable, "-m", "pytest", 
            "unit/test_basic_functionality.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result1.returncode == 0:
            print("✅ 基本功能測試通過")
        else:
            print("❌ 基本功能測試失敗")
            print(result1.stdout)
            print(result1.stderr)
        
        print("\n2️⃣ 執行所有網站 Mock 測試...")
        result2 = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_all_sites.py::TestAllSitesIntegration::test_individual_site_scraping_mock", 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result2.returncode == 0:
            print("✅ 所有網站 Mock 測試通過")
        else:
            print("❌ 所有網站 Mock 測試失敗")
            print(result2.stdout)
            print(result2.stderr)
        
        print("\n3️⃣ 執行多網站並發測試...")
        result3 = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_all_sites.py::TestAllSitesIntegration::test_multiple_sites_concurrent_mock", 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result3.returncode == 0:
            print("✅ 多網站並發測試通過")
        else:
            print("❌ 多網站並發測試失敗")
            print(result3.stdout)
            print(result3.stderr)
        
        # 總結
        print("\n" + "="*60)
        total_tests = 3
        passed_tests = sum([result1.returncode == 0, result2.returncode == 0, result3.returncode == 0])
        
        print(f"📊 測試總結：{passed_tests}/{total_tests} 測試通過")
        
        if passed_tests == total_tests:
            print("🎉 所有測試都通過了！jobseeker 可以正常工作。")
            return 0
        else:
            print("⚠️  部分測試失敗，請檢查上面的錯誤訊息。")
            return 1
            
    except ImportError as e:
        print(f"❌ 導入錯誤：{e}")
        print("請確保已安裝測試依賴：pip install -r requirements-test.txt")
        return 1
    except Exception as e:
        print(f"❌ 執行錯誤：{e}")
        return 1

def show_help():
    """
    顯示幫助資訊
    """
    help_text = """
🔧 jobseeker 快速測試工具

這個腳本會執行以下測試：
1. 基本功能測試 - 驗證核心功能
2. 所有網站 Mock 測試 - 測試9個網站的爬蟲功能（使用模擬資料）
3. 多網站並發測試 - 測試同時爬取多個網站

使用方法：
  python quick_test.py        # 執行快速測試
  python quick_test.py --help # 顯示此幫助

支援的網站：
  • LinkedIn      - 專業社交網路平台
  • Indeed        - 全球最大求職網站
  • ZipRecruiter  - 美國求職平台
  • Glassdoor     - 公司評價和薪資資訊
  • Google Jobs   - Google 求職搜尋
  • Bayt          - 中東地區求職平台
  • Naukri        - 印度求職網站
  • BDJobs        - 孟加拉求職平台
  • Seek          - 澳洲求職網站

更多測試選項：
  python test_runner.py --help    # 完整測試執行器
  python run_tests.py --help      # 簡化測試腳本
  pytest test_all_sites.py -v     # 直接使用 pytest
"""
    print(help_text)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        show_help()
        sys.exit(0)
    
    exit_code = main()
    sys.exit(exit_code)
