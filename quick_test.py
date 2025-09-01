#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試執行器

提供簡單的介面來執行用戶提示測試案例

Author: JobSpy Team
Date: 2025-01-09
"""

import os
import sys
from pathlib import Path

def main():
    """
    主函數 - 提供互動式測試選擇
    """
    print("🚀 JobSpy 用戶提示測試快速執行器")
    print("=" * 50)
    
    # 可用的測試選項
    tests = {
        '1': {
            'name': '澳洲AI工程師測試',
            'description': '搜尋澳洲Sydney和Melbourne的AI Engineer工作',
            'script': 'tests_collection/user_prompt_tests/phase1_basic_tests/test_australia_ai_engineer.py'
        },
        '2': {
            'name': '亞洲AI工程師測試',
            'description': '搜尋台北和東京近7日創建的AI Engineer職位',
            'script': 'tests_collection/user_prompt_tests/phase1_basic_tests/test_asia_ai_engineer.py'
        },
        '3': {
            'name': '新加坡ML工程師測試',
            'description': '尋找新加坡和香港的Machine Learning Engineer職位，薪資範圍80k-150k USD',
            'script': 'tests_collection/user_prompt_tests/phase2_advanced_tests/test_singapore_ml_engineer.py'
        },
        '4': {
            'name': '完整測試套件',
            'description': '執行所有用戶提示測試',
            'script': 'run_user_prompt_tests.py',
            'args': '--all'
        }
    }
    
    print("\n📋 可用的測試選項:")
    for key, test in tests.items():
        print(f"   {key}. {test['name']}")
        print(f"      {test['description']}")
        print()
    
    # 獲取用戶選擇
    while True:
        choice = input("請選擇要執行的測試 (1-4) 或 'q' 退出: ").strip()
        
        if choice.lower() == 'q':
            print("👋 再見!")
            return
        
        if choice in tests:
            selected_test = tests[choice]
            print(f"\n🎯 執行測試: {selected_test['name']}")
            print(f"📝 描述: {selected_test['description']}")
            print("\n⏳ 測試執行中...")
            
            # 執行測試
            script_path = selected_test['script']
            if os.path.exists(script_path):
                if choice == '4':  # 完整測試套件
                    command = f"python {script_path} {selected_test.get('args', '')}"
                else:
                    command = f"python {script_path}"
                
                print(f"執行命令: {command}")
                os.system(command)
            else:
                print(f"❌ 找不到測試腳本: {script_path}")
            
            print("\n" + "=" * 50)
            continue_choice = input("是否繼續執行其他測試? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
        else:
            print("❌ 無效選擇，請重新輸入")
    
    print("\n🎉 測試完成!")
    print("📁 測試結果保存在: tests_collection/user_prompt_tests/")


if __name__ == "__main__":
    main()