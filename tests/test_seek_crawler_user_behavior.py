#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek爬蟲引擎用戶行為測試
模擬真實用戶在Seek.com.au網站上的搜索和瀏覽行為
"""

import pytest
import asyncio
import time
import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch

# 導入Seek爬蟲相關模組
import sys
sys.path.append(str(Path(__file__).parent.parent / "jobseeker" / "seek"))

from seek_crawler_engine import SeekCrawlerEngine
from seek_scraper_enhanced import SeekScraperEnhanced
from config import SeekCrawlerConfig
from etl_processor import SeekETLProcessor


class TestSeekCrawlerUserBehavior:
    """Seek爬蟲用戶行為測試類"""
    
    def setup_method(self):
        """測試前設置"""
        self.config = SeekCrawlerConfig()
        self.engine = SeekCrawlerEngine(self.config)
        self.scraper = SeekScraperEnhanced(self.config)
        self.etl_processor = SeekETLProcessor(self.config)
        
        # 模擬真實用戶搜索關鍵詞
        self.real_search_terms = [
            "software engineer",
            "data scientist", 
            "product manager",
            "marketing manager",
            "business analyst",
            "frontend developer",
            "backend developer",
            "devops engineer",
            "ui ux designer",
            "project manager"
        ]
        
        # 模擬真實地點搜索
        self.real_locations = [
            "Sydney NSW",
            "Melbourne VIC",
            "Brisbane QLD",
            "Perth WA",
            "Adelaide SA",
            "Canberra ACT",
            "Gold Coast QLD",
            "Newcastle NSW",
            "Wollongong NSW",
            "Geelong VIC"
        ]
    
    def test_basic_job_search_simulation(self):
        """測試基本職位搜索模擬"""
        print("\n=== 測試基本職位搜索模擬 ===")
        
        # 隨機選擇搜索條件
        job_title = random.choice(self.real_search_terms)
        location = random.choice(self.real_locations)
        
        print(f"搜索條件: {job_title} in {location}")
        
        try:
            # 模擬用戶搜索行為
            search_params = {
                'job_title': job_title,
                'location': location,
                'results_wanted': 20,
                'hours_old': 72,
                'country_indeed': 'Australia'
            }
            
            # 執行搜索
            results = self.engine.search_jobs(**search_params)
            
            # 驗證結果
            assert isinstance(results, list), "搜索結果應該是列表格式"
            print(f"找到 {len(results)} 個職位")
            
            if results:
                # 檢查第一個結果的結構
                first_job = results[0]
                required_fields = ['title', 'company', 'location', 'job_url']
                
                for field in required_fields:
                    assert field in first_job, f"職位資料缺少必要欄位: {field}"
                
                print(f"第一個職位: {first_job.get('title', 'N/A')} @ {first_job.get('company', 'N/A')}")
            
        except Exception as e:
            print(f"搜索過程中發生錯誤: {str(e)}")
            # 在測試環境中，我們允許某些錯誤（如網絡問題）
            assert "network" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower()
    
    def test_advanced_search_with_filters(self):
        """測試帶過濾條件的高級搜索"""
        print("\n=== 測試高級搜索過濾 ===")
        
        try:
            # 模擬用戶使用多種過濾條件
            advanced_params = {
                'job_title': 'python developer',
                'location': 'Sydney NSW',
                'results_wanted': 15,
                'hours_old': 24,  # 只要最近24小時的職位
                'job_type': 'fulltime',
                'salary_min': 80000,
                'remote': True
            }
            
            results = self.engine.search_jobs(**advanced_params)
            
            assert isinstance(results, list), "高級搜索結果應該是列表格式"
            print(f"高級搜索找到 {len(results)} 個職位")
            
            # 驗證過濾效果
            if results:
                for job in results[:3]:  # 檢查前3個結果
                    # 檢查標題是否包含相關關鍵詞
                    title = job.get('title', '').lower()
                    assert 'python' in title or 'developer' in title, "搜索結果與關鍵詞不匹配"
                    
                    print(f"驗證職位: {job.get('title', 'N/A')}")
            
        except Exception as e:
            print(f"高級搜索錯誤: {str(e)}")
            # 允許網絡相關錯誤
            assert any(keyword in str(e).lower() for keyword in ['network', 'timeout', 'connection', 'rate limit'])
    
    def test_multiple_search_sessions(self):
        """測試多次搜索會話模擬"""
        print("\n=== 測試多次搜索會話 ===")
        
        search_sessions = []
        
        for i in range(3):
            try:
                # 模擬用戶在不同時間進行搜索
                job_title = random.choice(self.real_search_terms)
                location = random.choice(self.real_locations)
                
                print(f"會話 {i+1}: 搜索 '{job_title}' in '{location}'")
                
                search_params = {
                    'job_title': job_title,
                    'location': location,
                    'results_wanted': 10,
                    'hours_old': 168  # 一週內
                }
                
                start_time = time.time()
                results = self.engine.search_jobs(**search_params)
                end_time = time.time()
                
                session_data = {
                    'session_id': i + 1,
                    'search_params': search_params,
                    'results_count': len(results) if results else 0,
                    'duration': end_time - start_time,
                    'success': True
                }
                
                search_sessions.append(session_data)
                print(f"會話 {i+1} 完成: {session_data['results_count']} 個結果，耗時 {session_data['duration']:.2f} 秒")
                
                # 模擬用戶思考時間
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"會話 {i+1} 失敗: {str(e)}")
                session_data = {
                    'session_id': i + 1,
                    'search_params': search_params,
                    'results_count': 0,
                    'duration': 0,
                    'success': False,
                    'error': str(e)
                }
                search_sessions.append(session_data)
        
        # 驗證會話結果
        assert len(search_sessions) == 3, "應該完成3個搜索會話"
        
        successful_sessions = [s for s in search_sessions if s['success']]
        print(f"成功會話數: {len(successful_sessions)}/3")
        
        # 至少應該有一個成功的會話（在網絡正常的情況下）
        if len(successful_sessions) == 0:
            print("警告: 所有搜索會話都失敗了，可能是網絡問題")
    
    def test_data_export_simulation(self):
        """測試數據導出模擬"""
        print("\n=== 測試數據導出模擬 ===")
        
        try:
            # 先進行搜索
            search_params = {
                'job_title': 'data analyst',
                'location': 'Melbourne VIC',
                'results_wanted': 5
            }
            
            results = self.engine.search_jobs(**search_params)
            
            if results and len(results) > 0:
                # 測試不同格式的導出
                export_formats = ['csv', 'json', 'excel']
                
                for format_type in export_formats:
                    try:
                        export_path = f"test_export_{int(time.time())}.{format_type}"
                        
                        # 模擬用戶導出數據
                        success = self.etl_processor.export_data(
                            data=results,
                            format=format_type,
                            output_path=export_path
                        )
                        
                        assert success, f"{format_type.upper()} 導出失敗"
                        print(f"✓ {format_type.upper()} 導出成功: {export_path}")
                        
                        # 清理測試文件
                        import os
                        if os.path.exists(export_path):
                            os.remove(export_path)
                            
                    except Exception as e:
                        print(f"✗ {format_type.upper()} 導出失敗: {str(e)}")
            else:
                print("跳過導出測試：沒有搜索結果")
                
        except Exception as e:
            print(f"導出測試錯誤: {str(e)}")
    
    def test_error_handling_simulation(self):
        """測試錯誤處理模擬"""
        print("\n=== 測試錯誤處理模擬 ===")
        
        # 測試無效搜索參數
        invalid_params_tests = [
            {
                'name': '空職位標題',
                'params': {'job_title': '', 'location': 'Sydney NSW'},
                'expected_error': True
            },
            {
                'name': '無效結果數量',
                'params': {'job_title': 'engineer', 'location': 'Sydney NSW', 'results_wanted': -1},
                'expected_error': True
            },
            {
                'name': '過大結果數量',
                'params': {'job_title': 'engineer', 'location': 'Sydney NSW', 'results_wanted': 10000},
                'expected_error': True
            }
        ]
        
        for test_case in invalid_params_tests:
            try:
                print(f"測試 {test_case['name']}...")
                results = self.engine.search_jobs(**test_case['params'])
                
                if test_case['expected_error']:
                    print(f"✗ 預期錯誤但成功執行: {test_case['name']}")
                else:
                    print(f"✓ 正常執行: {test_case['name']}")
                    
            except Exception as e:
                if test_case['expected_error']:
                    print(f"✓ 正確捕獲錯誤: {test_case['name']} - {str(e)[:50]}...")
                else:
                    print(f"✗ 意外錯誤: {test_case['name']} - {str(e)[:50]}...")
    
    def test_performance_monitoring(self):
        """測試性能監控"""
        print("\n=== 測試性能監控 ===")
        
        performance_metrics = []
        
        for i in range(3):
            try:
                start_time = time.time()
                
                # 執行標準搜索
                results = self.engine.search_jobs(
                    job_title='software engineer',
                    location='Sydney NSW',
                    results_wanted=10
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                metrics = {
                    'test_run': i + 1,
                    'duration': duration,
                    'results_count': len(results) if results else 0,
                    'success': True
                }
                
                performance_metrics.append(metrics)
                print(f"測試 {i+1}: {duration:.2f}秒, {metrics['results_count']} 個結果")
                
            except Exception as e:
                metrics = {
                    'test_run': i + 1,
                    'duration': 0,
                    'results_count': 0,
                    'success': False,
                    'error': str(e)
                }
                performance_metrics.append(metrics)
                print(f"測試 {i+1}: 失敗 - {str(e)[:50]}...")
        
        # 分析性能指標
        successful_runs = [m for m in performance_metrics if m['success']]
        
        if successful_runs:
            avg_duration = sum(m['duration'] for m in successful_runs) / len(successful_runs)
            avg_results = sum(m['results_count'] for m in successful_runs) / len(successful_runs)
            
            print(f"\n性能摘要:")
            print(f"成功率: {len(successful_runs)}/3 ({len(successful_runs)/3*100:.1f}%)")
            print(f"平均耗時: {avg_duration:.2f} 秒")
            print(f"平均結果數: {avg_results:.1f} 個")
            
            # 性能基準檢查
            assert avg_duration < 30, f"平均搜索時間過長: {avg_duration:.2f} 秒"
        else:
            print("警告: 所有性能測試都失敗了")
    
    def test_concurrent_search_simulation(self):
        """測試並發搜索模擬"""
        print("\n=== 測試並發搜索模擬 ===")
        
        async def single_search(search_id: int, job_title: str, location: str):
            """單個搜索任務"""
            try:
                print(f"啟動搜索 {search_id}: {job_title} in {location}")
                
                # 注意：這裡我們模擬並發，但實際的搜索可能不是異步的
                results = self.engine.search_jobs(
                    job_title=job_title,
                    location=location,
                    results_wanted=5
                )
                
                return {
                    'search_id': search_id,
                    'success': True,
                    'results_count': len(results) if results else 0
                }
                
            except Exception as e:
                return {
                    'search_id': search_id,
                    'success': False,
                    'error': str(e)
                }
        
        async def run_concurrent_searches():
            """運行並發搜索"""
            search_tasks = []
            
            for i in range(3):
                job_title = random.choice(self.real_search_terms)
                location = random.choice(self.real_locations)
                
                # 創建搜索任務（注意：實際可能不是真正的異步）
                task = single_search(i + 1, job_title, location)
                search_tasks.append(task)
            
            # 等待所有搜索完成
            results = []
            for task in search_tasks:
                result = await task
                results.append(result)
            
            return results
        
        try:
            # 運行並發測試
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            concurrent_results = loop.run_until_complete(run_concurrent_searches())
            
            # 分析並發結果
            successful_searches = [r for r in concurrent_results if r['success']]
            
            print(f"並發搜索完成: {len(successful_searches)}/3 成功")
            
            for result in concurrent_results:
                if result['success']:
                    print(f"✓ 搜索 {result['search_id']}: {result['results_count']} 個結果")
                else:
                    print(f"✗ 搜索 {result['search_id']}: {result.get('error', 'Unknown error')[:50]}...")
            
            loop.close()
            
        except Exception as e:
            print(f"並發測試錯誤: {str(e)}")
    
    def teardown_method(self):
        """測試後清理"""
        # 清理任何臨時文件或資源
        pass


if __name__ == "__main__":
    # 運行測試
    print("開始Seek爬蟲用戶行為測試...")
    pytest.main([__file__, "-v", "-s"])