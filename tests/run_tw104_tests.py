#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行測試運行腳本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_tw104_random_user import TestTW104RandomUser, TW104RandomUserTest


async def run_quick_test():
    """運行快速測試"""
    print("🚀 開始 104人力銀行快速測試...")
    
    test_runner = TW104RandomUserTest()
    
    # 測試單個用戶會話
    user_profile = test_runner.simulator.get_random_user()
    behavior_pattern = test_runner.simulator.get_random_behavior()
    
    print(f"👤 測試用戶: {user_profile['type']} - {user_profile['id']}")
    print(f"🎭 行為模式: {behavior_pattern['name']}")
    
    session_result = await test_runner.simulate_user_session(user_profile, behavior_pattern)
    
    print(f"✅ 測試完成!")
    print(f"⏱️  會話時長: {session_result['duration']:.2f}秒")
    print(f"🎯 執行動作: {len(session_result['actions'])}個")
    print(f"❌ 錯誤數量: {len(session_result['errors'])}個")
    
    if session_result['errors']:
        print("錯誤詳情:")
        for error in session_result['errors']:
            print(f"  - {error['type']}: {error['message']}")
    
    return session_result


async def run_full_test():
    """運行完整測試"""
    print("🚀 開始 104人力銀行完整測試...")
    
    test_runner = TW104RandomUserTest()
    
    # 測試多個用戶會話
    session_count = 5
    for i in range(session_count):
        print(f"\n🎯 執行第 {i+1}/{session_count} 個會話...")
        
        user_profile = test_runner.simulator.get_random_user()
        behavior_pattern = test_runner.simulator.get_random_behavior()
        
        print(f"👤 用戶: {user_profile['type']} - {user_profile['id']}")
        print(f"🎭 行為: {behavior_pattern['name']}")
        
        session_result = await test_runner.simulate_user_session(user_profile, behavior_pattern)
        test_runner.test_results.append(session_result)
        
        print(f"✅ 會話 {i+1} 完成 - 時長: {session_result['duration']:.2f}秒")
        print(f"🎯 動作數: {len(session_result['actions'])}個")
        print(f"❌ 錯誤數: {len(session_result['errors'])}個")
        
        # 會話間隔
        if i < session_count - 1:
            delay = 5.0
            print(f"⏳ 等待 {delay} 秒後繼續...")
            await asyncio.sleep(delay)
    
    # 生成報告
    print("\n📊 生成測試報告...")
    test_instance = TestTW104RandomUser()
    test_instance.test_generate_test_report(test_runner)
    
    return test_runner.test_results


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="104人力銀行測試運行器")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick",
                       help="測試模式: quick (快速) 或 full (完整)")
    parser.add_argument("--headless", action="store_true",
                       help="無頭模式運行")
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        asyncio.run(run_quick_test())
    else:
        asyncio.run(run_full_test())


if __name__ == "__main__":
    main()
