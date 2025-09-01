#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 測試腳本批次執行器 (Python 版本)
用於一次執行所有測試腳本並生成統合報告
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
import json

def print_header():
    """
    顯示程式標題
    """
    print("=" * 60)
    print("🚀 JobSpy 測試腳本批次執行器")
    print("=" * 60)
    print("開始執行所有測試腳本...\n")

def create_batch_result_dir():
    """
    創建批次測試結果目錄
    
    Returns:
        str: 結果目錄路徑
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = f"batch_test_results_{timestamp}"
    Path(batch_dir).mkdir(exist_ok=True)
    print(f"📁 批次測試結果將保存到: {batch_dir}\n")
    return batch_dir

def get_test_scripts():
    """
    獲取測試腳本列表
    
    Returns:
        list: 測試腳本配置列表
    """
    return [
        {
            "name": "UI/UX 職位搜尋測試",
            "script": "ui_ux_test.py",
            "priority": "High",
            "description": "測試 UI/UX 相關職位的搜尋功能"
        },
        {
            "name": "機器學習工程師職位測試（最終版）",
            "script": "ml_engineer_test_final.py",
            "priority": "High",
            "description": "測試機器學習工程師職位搜尋功能"
        },
        {
            "name": "增強版爬蟲測試（最終版）",
            "script": "test_enhanced_scrapers_final.py",
            "priority": "Medium",
            "description": "測試增強版爬蟲的反檢測功能"
        },
        {
            "name": "簡化版增強爬蟲測試",
            "script": "simple_test.py",
            "priority": "Medium",
            "description": "簡化版的增強爬蟲功能測試"
        },
        {
            "name": "最終驗證測試",
            "script": "final_verification_test.py",
            "priority": "Low",
            "description": "最終功能驗證測試"
        },
        {
            "name": "BDJobs 修復測試",
            "script": "test_bdjobs_fix.py",
            "priority": "Low",
            "description": "BDJobs 網站特定修復測試"
        }
    ]

def run_single_test(test_config, batch_dir):
    """
    執行單個測試腳本
    
    Args:
        test_config (dict): 測試配置
        batch_dir (str): 批次結果目錄
    
    Returns:
        dict: 測試結果
    """
    print(f"\n--- 🧪 執行: {test_config['name']} ---")
    print(f"📄 腳本: {test_config['script']}")
    print(f"⭐ 優先級: {test_config['priority']}")
    print(f"📝 描述: {test_config['description']}")
    
    start_time = time.time()
    
    try:
        # 檢查腳本是否存在
        if not os.path.exists(test_config['script']):
            print(f"❌ 腳本檔案不存在: {test_config['script']}")
            return {
                'name': test_config['name'],
                'script': test_config['script'],
                'status': 'File Not Found',
                'duration': 0,
                'error': f"腳本檔案不存在: {test_config['script']}"
            }
        
        # 執行測試腳本
        result = subprocess.run(
            [sys.executable, test_config['script']],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 保存輸出
        output_file = os.path.join(batch_dir, f"{test_config['script']}_output.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 標準輸出 ===\n")
            f.write(result.stdout)
            f.write(f"\n\n=== 錯誤輸出 ===\n")
            f.write(result.stderr)
            f.write(f"\n\n=== 執行資訊 ===\n")
            f.write(f"退出代碼: {result.returncode}\n")
            f.write(f"執行時間: {duration:.2f} 秒\n")
        
        if result.returncode == 0:
            print(f"✅ 測試成功完成 ({duration:.1f}秒)")
            status = 'Success'
        else:
            print(f"❌ 測試執行失敗 (退出代碼: {result.returncode}, {duration:.1f}秒)")
            status = 'Failed'
            
        return {
            'name': test_config['name'],
            'script': test_config['script'],
            'priority': test_config['priority'],
            'status': status,
            'duration': duration,
            'return_code': result.returncode,
            'output_file': output_file
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ 測試執行異常: {str(e)} ({duration:.1f}秒)")
        
        # 保存錯誤信息
        error_file = os.path.join(batch_dir, f"{test_config['script']}_error.txt")
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"執行異常: {str(e)}\n")
            f.write(f"執行時間: {duration:.2f} 秒\n")
        
        return {
            'name': test_config['name'],
            'script': test_config['script'],
            'priority': test_config['priority'],
            'status': 'Error',
            'duration': duration,
            'error': str(e),
            'error_file': error_file
        }

def generate_report(test_results, batch_dir, total_duration):
    """
    生成測試報告
    
    Args:
        test_results (list): 測試結果列表
        batch_dir (str): 批次結果目錄
        total_duration (float): 總執行時間
    """
    successful_tests = len([r for r in test_results if r['status'] == 'Success'])
    failed_tests = len(test_results) - successful_tests
    success_rate = (successful_tests / len(test_results)) * 100
    
    # 生成文字報告
    report_file = os.path.join(batch_dir, "batch_test_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("JobSpy 批次測試報告\n")
        f.write("=" * 50 + "\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"總執行時間: {total_duration:.1f} 秒\n")
        f.write(f"測試腳本數量: {len(test_results)}\n")
        f.write(f"成功測試: {successful_tests}\n")
        f.write(f"失敗測試: {failed_tests}\n")
        f.write(f"成功率: {success_rate:.1f}%\n\n")
        
        f.write("詳細結果:\n")
        f.write("=" * 50 + "\n")
        
        for result in test_results:
            f.write(f"\n測試名稱: {result['name']}\n")
            f.write(f"腳本檔案: {result['script']}\n")
            f.write(f"優先級: {result['priority']}\n")
            f.write(f"狀態: {result['status']}\n")
            f.write(f"執行時間: {result['duration']:.2f} 秒\n")
            if 'error' in result:
                f.write(f"錯誤: {result['error']}\n")
            f.write("-" * 30 + "\n")
    
    # 生成 JSON 報告
    json_file = os.path.join(batch_dir, "batch_test_report.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_tests': len(test_results),
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'total_duration': total_duration,
                'timestamp': datetime.now().isoformat()
            },
            'results': test_results
        }, f, indent=2, ensure_ascii=False)
    
    return report_file, json_file

def main():
    """
    主函數 - 執行批次測試
    """
    print_header()
    
    # 創建結果目錄
    batch_dir = create_batch_result_dir()
    
    # 獲取測試腳本列表
    test_scripts = get_test_scripts()
    
    # 執行測試
    test_results = []
    start_time = time.time()
    
    for test_config in test_scripts:
        result = run_single_test(test_config, batch_dir)
        test_results.append(result)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 生成報告
    report_file, json_file = generate_report(test_results, batch_dir, total_duration)
    
    # 顯示最終結果
    print("\n" + "=" * 60)
    print("🎉 批次測試完成")
    print("=" * 60)
    
    successful_tests = len([r for r in test_results if r['status'] == 'Success'])
    failed_tests = len(test_results) - successful_tests
    success_rate = (successful_tests / len(test_results)) * 100
    
    print(f"⏱️  總執行時間: {total_duration:.1f} 秒")
    print(f"✅ 成功測試: {successful_tests}/{len(test_results)}")
    print(f"❌ 失敗測試: {failed_tests}/{len(test_results)}")
    print(f"📊 成功率: {success_rate:.1f}%")
    
    # 顯示測試結果摘要
    print("\n📋 測試結果摘要:")
    print("-" * 80)
    print(f"{'測試名稱':<30} {'狀態':<10} {'時間(秒)':<10} {'優先級':<10}")
    print("-" * 80)
    
    for result in test_results:
        status_icon = "✅" if result['status'] == 'Success' else "❌"
        print(f"{result['name'][:29]:<30} {status_icon} {result['status']:<8} {result['duration']:<9.1f} {result['priority']:<10}")
    
    print(f"\n📄 詳細報告: {report_file}")
    print(f"📊 JSON 報告: {json_file}")
    print(f"📁 所有輸出: {batch_dir}")
    
    # 失敗測試建議
    if failed_tests > 0:
        print("\n⚠️  建議檢查失敗的測試:")
        for result in test_results:
            if result['status'] != 'Success':
                print(f"   - {result['name']} ({result['script']})")
    
    print("\n🚀 批次測試執行完成！")

if __name__ == "__main__":
    main()