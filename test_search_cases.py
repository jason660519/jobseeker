#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索功能測試案例
測試JobSeeker網頁應用的搜索欄功能
"""

import requests
import json
import time
from typing import List, Dict, Any

class SearchTestCases:
    """搜索功能測試案例類"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """初始化測試案例
        
        Args:
            base_url: 網頁應用的基礎URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_search_endpoint(self, query: str, location: str = "台北") -> Dict[str, Any]:
        """測試搜索端點
        
        Args:
            query: 搜索關鍵字
            location: 搜索地點
            
        Returns:
            測試結果字典
        """
        try:
            # 準備搜索數據
            search_data = {
                'query': query,
                'location': location,
                'site': 'seek'  # 預設使用seek網站
            }
            
            print(f"\n🔍 測試搜索: '{query}' 在 '{location}'")
            
            # 發送POST請求到搜索端點
            response = self.session.post(
                f"{self.base_url}/search",
                data=search_data,
                timeout=30
            )
            
            # 檢查響應狀態
            if response.status_code == 200:
                print(f"✅ 搜索請求成功 (狀態碼: {response.status_code})")
                
                # 嘗試解析JSON響應
                try:
                    result = response.json()
                    job_count = len(result.get('jobs', []))
                    print(f"📊 找到 {job_count} 個職位")
                    
                    return {
                        'status': 'success',
                        'query': query,
                        'location': location,
                        'job_count': job_count,
                        'response_time': response.elapsed.total_seconds(),
                        'data': result
                    }
                except json.JSONDecodeError:
                    print(f"⚠️ 響應不是有效的JSON格式")
                    return {
                        'status': 'json_error',
                        'query': query,
                        'location': location,
                        'response_text': response.text[:500]
                    }
            else:
                print(f"❌ 搜索請求失敗 (狀態碼: {response.status_code})")
                return {
                    'status': 'http_error',
                    'query': query,
                    'location': location,
                    'status_code': response.status_code,
                    'error_text': response.text[:500]
                }
                
        except requests.exceptions.RequestException as e:
            print(f"🚫 網絡請求錯誤: {str(e)}")
            return {
                'status': 'network_error',
                'query': query,
                'location': location,
                'error': str(e)
            }
    
    def run_test_suite(self) -> List[Dict[str, Any]]:
        """運行完整的測試套件
        
        Returns:
            所有測試結果的列表
        """
        print("🚀 開始運行搜索功能測試套件")
        print("=" * 60)
        
        # 定義測試案例
        test_cases = [
            # 基本職位搜索
            {"query": "軟體工程師", "location": "台北"},
            {"query": "Python開發者", "location": "新竹"},
            {"query": "前端工程師", "location": "台中"},
            {"query": "資料科學家", "location": "高雄"},
            
            # 英文職位搜索
            {"query": "Software Engineer", "location": "Taipei"},
            {"query": "Data Analyst", "location": "Taichung"},
            {"query": "Product Manager", "location": "Kaohsiung"},
            
            # 特殊字符和邊界案例
            {"query": "AI/ML工程師", "location": "台北"},
            {"query": "C++開發者", "location": "新竹"},
            {"query": "UI/UX設計師", "location": "台中"},
            
            # 空白和特殊情況
            {"query": "", "location": "台北"},  # 空查詢
            {"query": "   ", "location": "台北"},  # 空白查詢
            {"query": "工程師", "location": ""},  # 空地點
            
            # 長查詢測試
            {"query": "資深全端軟體開發工程師具備React Node.js經驗", "location": "台北"},
        ]
        
        results = []
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📋 測試案例 {i}/{len(test_cases)}")
            result = self.test_search_endpoint(case["query"], case["location"])
            results.append(result)
            
            # 在測試之間稍作停頓，避免過度請求
            time.sleep(1)
        
        return results
    
    def generate_test_report(self, results: List[Dict[str, Any]]) -> None:
        """生成測試報告
        
        Args:
            results: 測試結果列表
        """
        print("\n" + "=" * 60)
        print("📊 測試報告摘要")
        print("=" * 60)
        
        total_tests = len(results)
        successful_tests = len([r for r in results if r['status'] == 'success'])
        failed_tests = total_tests - successful_tests
        
        print(f"總測試數量: {total_tests}")
        print(f"成功測試: {successful_tests}")
        print(f"失敗測試: {failed_tests}")
        print(f"成功率: {(successful_tests/total_tests)*100:.1f}%")
        
        # 詳細結果分析
        print("\n📈 詳細結果:")
        for i, result in enumerate(results, 1):
            status_icon = "✅" if result['status'] == 'success' else "❌"
            query = result['query'] if result['query'] else "[空查詢]"
            location = result['location'] if result['location'] else "[空地點]"
            
            if result['status'] == 'success':
                job_count = result.get('job_count', 0)
                response_time = result.get('response_time', 0)
                print(f"{status_icon} 測試 {i}: '{query}' @ '{location}' - {job_count} 職位 ({response_time:.2f}s)")
            else:
                error_type = result['status']
                print(f"{status_icon} 測試 {i}: '{query}' @ '{location}' - 錯誤: {error_type}")
        
        # 保存詳細結果到文件
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"search_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細測試結果已保存到: {report_file}")

def main():
    """主函數 - 運行搜索測試"""
    print("🎯 JobSeeker 搜索功能測試")
    print("測試目標: http://localhost:5000")
    
    # 創建測試實例
    tester = SearchTestCases()
    
    # 運行測試套件
    results = tester.run_test_suite()
    
    # 生成測試報告
    tester.generate_test_report(results)
    
    print("\n🏁 測試完成!")

if __name__ == "__main__":
    main()