#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據完整性和輸出格式驗證測試

本測試檔案專注於驗證搜尋結果的數據完整性、格式正確性和輸出品質。
測試包括 CSV 格式驗證、數據欄位完整性、編碼正確性等。

作者: AI Assistant
創建時間: 2025年1月
"""

import pytest
import requests
import csv
import io
import re
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin


class TestDataIntegrityValidation:
    """數據完整性和輸出格式驗證測試類"""
    
    BASE_URL = "http://localhost:5000"
    
    def setup_method(self):
        """測試前的設置"""
        self.session = requests.Session()
        self.session.timeout = 45  # 增加超時時間以適應數據處理
        
    def teardown_method(self):
        """測試後的清理"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def _perform_search_and_get_response(self, search_params: Dict[str, str]) -> requests.Response:
        """執行搜尋並返回響應"""
        response = self.session.post(
            f"{self.BASE_URL}/search",
            data=search_params
        )
        return response
    
    def _extract_csv_download_link(self, html_content: str) -> Optional[str]:
        """從 HTML 內容中提取 CSV 下載連結"""
        # 尋找 CSV 下載連結的模式
        csv_patterns = [
            r'href="([^"]*\.csv[^"]*?)"',
            r'href="(/download/[^"]*?)"',
            r'href="(/static/[^"]*\.csv[^"]*?)"'
        ]
        
        for pattern in csv_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def test_search_result_data_structure(self):
        """測試搜尋結果的數據結構"""
        search_params = {
            'query': 'python developer',
            'location': 'taipei',
            'results_wanted': '25',
            'hours_old': '168'
        }
        
        response = self._perform_search_and_get_response(search_params)
        assert response.status_code == 200
        
        content = response.text
        
        # 檢查是否包含結果表格或結果區域
        result_indicators = [
            'table',
            'results',
            '結果',
            'job',
            '職位',
            'position',
            'title'
        ]
        
        content_lower = content.lower()
        found_indicators = sum(1 for indicator in result_indicators 
                             if indicator in content_lower)
        
        assert found_indicators >= 2, "Search results structure not found"
        
        # 檢查是否有適當的 JSON 結構
        response_data = response.json()
        assert 'jobs' in response_data, "響應應包含職位數據"
        assert isinstance(response_data['jobs'], list), "職位數據應為列表格式"
    
    def test_csv_output_availability(self):
        """測試 CSV 輸出的可用性"""
        search_params = {
            'query': 'data analyst',
            'location': 'taipei',
            'results_wanted': '10'
        }
        
        response = self._perform_search_and_get_response(search_params)
        assert response.status_code == 200
        
        content = response.text
        
        # 檢查是否有 CSV 下載選項
        csv_indicators = [
            'csv',
            'download',
            '下載',
            'export',
            '匯出'
        ]
        
        content_lower = content.lower()
        has_csv_option = any(indicator in content_lower for indicator in csv_indicators)
        
        # 如果有 CSV 選項，測試其功能
        if has_csv_option:
            csv_link = self._extract_csv_download_link(content)
            if csv_link:
                # 測試 CSV 下載
                csv_url = urljoin(self.BASE_URL, csv_link)
                csv_response = self.session.get(csv_url)
                
                if csv_response.status_code == 200:
                    # 驗證 CSV 格式
                    self._validate_csv_format(csv_response.text)
    
    def _validate_csv_format(self, csv_content: str):
        """驗證 CSV 格式的正確性"""
        try:
            # 使用 StringIO 來模擬檔案
            csv_file = io.StringIO(csv_content)
            reader = csv.reader(csv_file)
            
            rows = list(reader)
            assert len(rows) > 0, "CSV file is empty"
            
            # 檢查標題行
            headers = rows[0] if rows else []
            expected_headers = [
                'title', 'company', 'location', 'date_posted', 
                'job_url', 'salary', 'description'
            ]
            
            # 至少應該包含一些基本欄位
            header_lower = [h.lower() for h in headers]
            basic_fields_found = sum(1 for field in ['title', 'company', 'location'] 
                                   if any(field in h for h in header_lower))
            
            assert basic_fields_found >= 2, f"Missing basic fields in CSV headers: {headers}"
            
            # 檢查數據行
            if len(rows) > 1:
                data_rows = rows[1:]
                for i, row in enumerate(data_rows[:3]):  # 檢查前3行
                    assert len(row) == len(headers), f"Row {i+1} has inconsistent column count"
                    
                    # 檢查是否有基本數據
                    non_empty_cells = sum(1 for cell in row if cell.strip())
                    assert non_empty_cells > 0, f"Row {i+1} is completely empty"
            
        except csv.Error as e:
            pytest.fail(f"CSV format validation failed: {e}")
    
    def test_data_encoding_integrity(self):
        """測試數據編碼的完整性"""
        search_params = {
            'query': '軟體工程師',  # 使用中文搜尋詞
            'location': '台北',
            'results_wanted': '10'
        }
        
        response = self._perform_search_and_get_response(search_params)
        assert response.status_code == 200
        
        content = response.text
        
        # 檢查中文字符是否正確顯示
        response_data = response.json()
        response_str = str(response_data)
        
        # 檢查是否包含中文字符（可能在職位描述或公司名稱中）
        has_chinese = any(ord(char) > 127 for char in response_str)
        # 如果沒有中文字符，至少應該有英文職位相關詞彙
        english_keywords = ['software', 'engineer', 'developer', 'programmer', 'job', 'position']
        has_job_keywords = any(keyword.lower() in response_str.lower() for keyword in english_keywords)
        
        assert has_chinese or has_job_keywords, f"響應中應包含職位相關關鍵字，實際內容: {response_str[:200]}..."
        
        # 檢查 JSON 編碼
        assert response.headers.get('content-type', '').startswith('application/json')
        
        # 檢查是否有亂碼
        problematic_patterns = [
            '\ufffd',  # 替換字符
            '???',     # 常見亂碼
            '\\x',    # 轉義字符洩漏
        ]
        
        for pattern in problematic_patterns:
            assert pattern not in content, f"Encoding issue detected: {pattern}"
    
    def test_job_data_completeness(self):
        """測試職位數據的完整性"""
        search_params = {
            'query': 'software engineer',
            'location': 'taipei',
            'results_wanted': '25'
        }
        
        response = self._perform_search_and_get_response(search_params)
        assert response.status_code == 200
        
        content = response.text
        
        # 檢查是否包含職位相關的關鍵信息
        job_data_indicators = [
            'software',
            'engineer',
            'taipei',
            'company',
            'salary',
            'description',
            'date',
            'url',
            'link'
        ]
        
        content_lower = content.lower()
        found_indicators = sum(1 for indicator in job_data_indicators 
                             if indicator in content_lower)
        
        # 至少應該找到一半的指標
        assert found_indicators >= len(job_data_indicators) // 2, \
            f"Insufficient job data indicators found: {found_indicators}/{len(job_data_indicators)}"
    
    def test_search_result_consistency(self):
        """測試搜尋結果的一致性"""
        search_params = {
            'query': 'python',
            'location': 'taipei',
            'results_wanted': '10'
        }
        
        # 執行兩次相同的搜尋
        response1 = self._perform_search_and_get_response(search_params)
        time.sleep(2)  # 短暫等待
        response2 = self._perform_search_and_get_response(search_params)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        content1 = response1.text
        content2 = response2.text
        
        # 檢查基本結構是否一致
        structure_elements = ['<table', '<div', 'class=', 'python', 'taipei']
        
        for element in structure_elements:
            in_content1 = element.lower() in content1.lower()
            in_content2 = element.lower() in content2.lower()
            
            # 基本結構應該保持一致
            assert in_content1 == in_content2, f"Inconsistent structure for element: {element}"
    
    def test_error_message_quality(self):
        """測試錯誤信息的品質"""
        # 測試各種錯誤情況的信息品質
        error_cases = [
            {
                'params': {
                    'query': '',
                    'location': 'taipei'
                },
                'expected_error_type': 'empty_query'
            },
            {
                'params': {
                    'query': 'test',
                    'location': '',
                    'results_wanted': '0'
                },
                'expected_error_type': 'invalid_parameters'
            },
            {
                'params': {
                    'query': 'test',
                    'location': 'taipei',
                    'results_wanted': '-5'
                },
                'expected_error_type': 'negative_results'
            }
        ]
        
        for i, case in enumerate(error_cases):
            response = self._perform_search_and_get_response(case['params'])
            
            # 不應該是伺服器錯誤
            assert response.status_code != 500, f"Error case {i+1} caused server error"
            
            content = response.text
            
            # 檢查錯誤信息的品質
            if response.status_code != 200:
                # 應該有有意義的錯誤信息
                error_indicators = ['error', '錯誤', 'invalid', '無效', 'required', '必需']
                has_error_message = any(indicator in content.lower() 
                                      for indicator in error_indicators)
                
                assert has_error_message, f"Error case {i+1} lacks proper error message"
    
    def test_output_html_validity(self):
        """測試輸出 HTML 的有效性"""
        search_params = {
            'query': 'developer',
            'location': 'taipei',
            'results_wanted': '10'
        }
        
        response = self._perform_search_and_get_response(search_params)
        assert response.status_code == 200
        
        content = response.text
        
        # 檢查基本 JSON 結構
        response_data = response.json()
        
        json_requirements = ['success', 'jobs', 'total_jobs']
        
        for field in json_requirements:
            assert field in response_data, f"Missing JSON field: {field}"
        
        # 檢查 JSON 數據類型正確性
        response_data = response.json()
        
        assert isinstance(response_data.get('success'), bool), "'success' field should be boolean"
        assert isinstance(response_data.get('jobs'), list), "'jobs' field should be a list"
        assert isinstance(response_data.get('total_jobs'), int), "'total_jobs' field should be an integer"
        
        # 檢查職位數據結構
        if response_data.get('jobs'):
            job = response_data['jobs'][0]
            expected_job_fields = ['title', 'company', 'location', 'date_posted']
            for field in expected_job_fields:
                if field in job:
                    assert isinstance(job[field], str), f"Job field '{field}' should be string"
    
    def test_performance_data_metrics(self):
        """測試性能數據指標"""
        search_params = {
            'query': 'data scientist',
            'location': 'taipei',
            'results_wanted': '25'
        }
        
        # 測量搜尋性能
        start_time = time.time()
        response = self._perform_search_and_get_response(search_params)
        end_time = time.time()
        
        search_duration = end_time - start_time
        
        assert response.status_code == 200
        
        # 記錄性能指標
        content_size = len(response.content)
        
        print(f"\nData Integrity Performance Metrics:")
        print(f"Search duration: {search_duration:.2f} seconds")
        print(f"Response size: {content_size} bytes")
        print(f"Content type: {response.headers.get('content-type', 'unknown')}")
        
        # 性能斷言
        assert search_duration < 60, f"Search took too long: {search_duration:.2f} seconds"
        assert content_size > 1000, "Response content seems too small"
        assert content_size < 10 * 1024 * 1024, "Response content seems too large (>10MB)"
    
    def test_multiple_site_data_consistency(self):
        """測試多個網站的數據一致性"""
        # 測試不同的搜尋組合
        test_combinations = [
            {'query': 'software engineer', 'location': 'taipei'},
            {'query': 'data scientist', 'location': 'singapore'}
        ]
        
        results = {}
        
        for i, combination in enumerate(test_combinations):
            search_params = {
                'query': combination['query'],
                'location': combination['location'],
                'results_wanted': '10'
            }
            
            try:
                response = self._perform_search_and_get_response(search_params)
                
                test_name = f"test_{i+1}"
                query_terms = combination['query'].lower().split()
                
                results[test_name] = {
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'has_results': any(term in response.text.lower() for term in query_terms),
                    'response_time': time.time(),
                    'query': combination['query'],
                    'location': combination['location']
                }
                
                # 添加請求間隔
                time.sleep(3)
                
            except Exception as e:
                results[test_name] = {
                    'status_code': None,
                    'error': str(e),
                    'query': combination['query'],
                    'location': combination['location']
                }
        
        # 驗證結果
        successful_tests = [test for test, result in results.items() 
                          if result.get('status_code') == 200]
        
        assert len(successful_tests) >= 1, f"No tests returned successful results: {results}"
        
        # 檢查成功的測試是否都有相關結果
        for test in successful_tests:
            assert results[test]['has_results'], f"Test {test} didn't return relevant results for query: {results[test]['query']}"


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "-s"])