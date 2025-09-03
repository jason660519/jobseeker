#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試搜尋功能的腳本
"""

import requests
import json

def test_search_api():
    """測試搜尋 API"""
    url = "http://localhost:5000/search"
    
    # 測試數據
    test_data = {
        "query": "軟體工程師",
        "location": "台北",
        "results_wanted": 5,
        "page": 1,
        "per_page": 5
    }
    
    print("🔍 測試搜尋 API...")
    print(f"請求 URL: {url}")
    print(f"請求數據: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"響應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 搜尋成功!")
            print(f"總職位數: {result.get('total_jobs', 0)}")
            print(f"搜尋 ID: {result.get('search_id', 'N/A')}")
            
            if result.get('jobs'):
                print(f"找到 {len(result['jobs'])} 個職位")
                for i, job in enumerate(result['jobs'][:3], 1):
                    print(f"  {i}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
            else:
                print("⚠️ 沒有找到職位")
                
            if result.get('routing_info'):
                routing = result['routing_info']
                print(f"執行時間: {routing.get('execution_time', 0):.2f} 秒")
                print(f"成功平台: {routing.get('successful_platforms', [])}")
                print(f"失敗平台: {routing.get('failed_platforms', [])}")
        else:
            print(f"❌ 搜尋失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保後端正在運行")
    except requests.exceptions.Timeout:
        print("❌ 請求超時")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

def test_health_api():
    """測試健康檢查 API"""
    url = "http://localhost:5000/health"
    
    print("\n🏥 測試健康檢查 API...")
    print(f"請求 URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"響應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 健康檢查通過!")
            print(f"狀態: {result.get('status', 'N/A')}")
            print(f"版本: {result.get('version', 'N/A')}")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始測試 JobSpy 搜尋功能\n")
    
    # 測試健康檢查
    test_health_api()
    
    # 測試搜尋功能
    test_search_api()
    
    print("\n✨ 測試完成!")
