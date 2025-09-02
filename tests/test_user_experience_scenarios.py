#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用戶體驗場景測試
模擬真實用戶的使用場景和體驗流程
"""

import pytest
import requests
import time
import random
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode


class TestUserExperienceScenarios:
    """用戶體驗場景測試類"""
    
    BASE_URL = "http://localhost:5000"
    
    def setup_method(self):
        """測試前設置"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UXTest/1.0 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def test_first_time_user_journey(self):
        """測試首次用戶使用流程"""
        # 1. 首次訪問首頁
        response = self.session.get(self.BASE_URL)
        assert response.status_code == 200
        assert "jobseeker" in response.text or "智能職位搜尋" in response.text
        
        # 檢查首頁是否包含必要的指導信息
        page_content = response.text.lower()
        assert any(keyword in page_content for keyword in [
            "search", "job", "title", "location", "submit", "find"
        ]), "首頁缺少基本的指導信息"
        
        # 2. 模擬新用戶的第一次搜尋（簡單查詢）
        first_search = {
            "job_title": "developer",
            "location": "usa",
            "results_wanted": 10
        }
        
        # 模擬用戶思考時間
        time.sleep(2)
        
        search_response = self.session.post(f"{self.BASE_URL}/search", data=first_search)
        assert search_response.status_code in [200, 400, 422]
        
        # 3. 檢查搜尋結果是否用戶友好
        if search_response.status_code == 200:
            result_content = search_response.text.lower()
            # 應該包含結果相關的信息
            assert any(keyword in result_content for keyword in [
                "result", "job", "found", "position", "company"
            ]), "搜尋結果頁面缺少清晰的結果信息"
    
    def test_experienced_user_workflow(self):
        """測試有經驗用戶的工作流程"""
        # 有經驗的用戶通常會使用更具體的搜尋條件
        advanced_searches = [
            {
                "job_title": "Senior Python Developer",
                "location": "canada",
                "results_wanted": 25,
                "hours_old": 48,
                "country_indeed": "canada"
            },
            {
                "job_title": "Machine Learning Engineer",
                "location": "uk",
                "results_wanted": 20,
                "hours_old": 72,
                "country_indeed": "uk"
            },
            {
                "job_title": "DevOps Engineer AWS",
                "location": "australia",
                "results_wanted": 15,
                "hours_old": 24,
                "country_indeed": "australia"
            }
        ]
        
        for i, search_data in enumerate(advanced_searches):
            # 模擬快速但深思熟慮的搜尋
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.post(f"{self.BASE_URL}/search", data=search_data)
            assert response.status_code in [200, 400, 422], f"高級搜尋 {i} 失敗"
            
            # 有經驗的用戶期望快速響應
            # 這裡可以添加響應時間檢查
    
    def test_job_seeker_persona_scenarios(self):
        """測試不同求職者角色的使用場景"""
        # 1. 應屆畢業生 - 尋找入門級職位
        graduate_searches = [
            {"job_title": "Junior Developer", "location": "usa", "results_wanted": 30},
            {"job_title": "Entry Level Software Engineer", "location": "canada", "results_wanted": 25},
            {"job_title": "Graduate Trainee", "location": "uk", "results_wanted": 20}
        ]
        
        for search in graduate_searches:
            response = self.session.post(f"{self.BASE_URL}/search", data=search)
            assert response.status_code in [200, 400, 422]
            time.sleep(1)
        
        # 2. 資深專業人士 - 尋找高級職位
        senior_searches = [
            {"job_title": "Senior Software Architect", "location": "usa", "results_wanted": 15},
            {"job_title": "Principal Engineer", "location": "canada", "results_wanted": 10},
            {"job_title": "Technical Lead", "location": "uk", "results_wanted": 12}
        ]
        
        for search in senior_searches:
            response = self.session.post(f"{self.BASE_URL}/search", data=search)
            assert response.status_code in [200, 400, 422]
            time.sleep(1)
        
        # 3. 職業轉換者 - 探索新領域
        career_change_searches = [
            {"job_title": "Data Analyst", "location": "usa", "results_wanted": 20},
            {"job_title": "Product Manager", "location": "canada", "results_wanted": 18},
            {"job_title": "UX Designer", "location": "uk", "results_wanted": 15}
        ]
        
        for search in career_change_searches:
            response = self.session.post(f"{self.BASE_URL}/search", data=search)
            assert response.status_code in [200, 400, 422]
            time.sleep(1)
    
    def test_international_user_scenarios(self):
        """測試國際用戶使用場景"""
        international_scenarios = [
            # 亞洲用戶
            {"job_title": "Software Engineer", "location": "singapore", "results_wanted": 20},
            {"job_title": "Data Scientist", "location": "japan", "results_wanted": 15},
            
            # 歐洲用戶
            {"job_title": "Frontend Developer", "location": "germany", "results_wanted": 25},
            {"job_title": "Backend Engineer", "location": "france", "results_wanted": 18},
            
            # 其他地區用戶
            {"job_title": "Full Stack Developer", "location": "brazil", "results_wanted": 22},
            {"job_title": "Mobile Developer", "location": "india", "results_wanted": 30}
        ]
        
        for scenario in international_scenarios:
            # 模擬不同時區的訪問模式
            time.sleep(random.uniform(0.3, 1.2))
            
            response = self.session.post(f"{self.BASE_URL}/search", data=scenario)
            assert response.status_code in [200, 400, 422]
            
            # 國際用戶可能需要更多時間來理解結果
            if response.status_code == 200:
                # 檢查是否有適當的國際化支持
                content = response.text.lower()
                # 基本檢查：結果應該是可理解的
                assert len(content) > 100, "國際用戶搜尋結果內容過少"
    
    def test_mobile_user_experience(self):
        """測試移動用戶體驗"""
        # 設置移動設備 User-Agent
        mobile_session = requests.Session()
        mobile_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        
        # 移動用戶通常進行簡短的搜尋
        mobile_searches = [
            {"job_title": "developer", "location": "usa", "results_wanted": 10},
            {"job_title": "engineer", "location": "canada", "results_wanted": 8},
            {"job_title": "analyst", "location": "uk", "results_wanted": 12}
        ]
        
        for search in mobile_searches:
            response = mobile_session.post(f"{self.BASE_URL}/search", data=search)
            assert response.status_code in [200, 400, 422]
            
            # 移動設備應該有適當的響應
            if response.status_code == 200:
                # 檢查移動友好性
                content = response.text.lower()
                # 基本檢查：頁面應該包含 viewport 或移動優化標籤
                mobile_friendly = any(keyword in content for keyword in [
                    "viewport", "mobile", "responsive"
                ])
                # 這個檢查可能需要根據實際實現調整
        
        mobile_session.close()
    
    def test_error_recovery_user_experience(self):
        """測試錯誤恢復的用戶體驗"""
        # 1. 用戶犯常見錯誤
        common_mistakes = [
            {"job_title": "", "location": "usa"},  # 忘記填寫職位
            {"job_title": "developer", "location": ""},  # 忘記填寫地點
            {"job_title": "developer", "location": "xyz"},  # 錯誤的地點
        ]
        
        for mistake in common_mistakes:
            error_response = self.session.post(f"{self.BASE_URL}/search", data=mistake)
            
            # 錯誤處理應該是用戶友好的
            if error_response.status_code >= 400:
                error_content = error_response.text.lower()
                # 應該有清晰的錯誤信息
                assert any(keyword in error_content for keyword in [
                    "error", "invalid", "required", "please", "try"
                ]), "錯誤信息不夠用戶友好"
        
        # 2. 用戶修正錯誤後重新嘗試
        corrected_search = {
            "job_title": "software developer",
            "location": "usa",
            "results_wanted": 15
        }
        
        corrected_response = self.session.post(f"{self.BASE_URL}/search", data=corrected_search)
        assert corrected_response.status_code in [200, 400, 422]
        
        # 3. 檢查應用是否從錯誤中完全恢復
        final_check = self.session.get(self.BASE_URL)
        assert final_check.status_code == 200
    
    def test_power_user_scenarios(self):
        """測試高級用戶使用場景"""
        # 高級用戶可能會進行複雜的搜尋組合
        power_user_searches = [
            {
                "job_title": "Senior Full Stack Developer React Node.js",
                "location": "usa",
                "results_wanted": 50,
                "hours_old": 24,
                "country_indeed": "usa"
            },
            {
                "job_title": "Principal Software Engineer Python AWS",
                "location": "canada",
                "results_wanted": 40,
                "hours_old": 48,
                "country_indeed": "canada"
            },
            {
                "job_title": "Lead Data Scientist Machine Learning",
                "location": "uk",
                "results_wanted": 35,
                "hours_old": 72,
                "country_indeed": "uk"
            }
        ]
        
        for search in power_user_searches:
            response = self.session.post(f"{self.BASE_URL}/search", data=search)
            assert response.status_code in [200, 400, 422]
            
            # 高級用戶期望詳細的結果
            if response.status_code == 200:
                # 檢查結果的豐富性
                content = response.text
                assert len(content) > 500, "高級搜尋結果內容不夠豐富"
            
            # 高級用戶通常會快速瀏覽多個搜尋
            time.sleep(random.uniform(0.2, 0.8))
    
    def test_casual_browser_scenarios(self):
        """測試隨意瀏覽者使用場景"""
        # 隨意瀏覽者可能會進行探索性搜尋
        casual_searches = [
            {"job_title": "remote work", "location": "usa", "results_wanted": 20},
            {"job_title": "part time", "location": "canada", "results_wanted": 15},
            {"job_title": "freelance", "location": "uk", "results_wanted": 25},
            {"job_title": "internship", "location": "australia", "results_wanted": 30}
        ]
        
        for search in casual_searches:
            # 隨意瀏覽者通常會有較長的思考時間
            time.sleep(random.uniform(1.0, 3.0))
            
            response = self.session.post(f"{self.BASE_URL}/search", data=search)
            assert response.status_code in [200, 400, 422]
            
            # 隨意瀏覽者可能會多次返回首頁
            if random.choice([True, False]):
                homepage_response = self.session.get(self.BASE_URL)
                assert homepage_response.status_code == 200
    
    def test_accessibility_scenarios(self):
        """測試無障礙訪問場景"""
        # 模擬使用輔助技術的用戶
        accessibility_session = requests.Session()
        accessibility_session.headers.update({
            'User-Agent': 'AccessibilityTest/1.0 ScreenReader Mozilla/5.0'
        })
        
        # 檢查首頁的無障礙性
        response = accessibility_session.get(self.BASE_URL)
        assert response.status_code == 200
        
        content = response.text.lower()
        
        # 基本無障礙檢查
        accessibility_indicators = [
            "alt=",  # 圖片替代文字
            "label",  # 表單標籤
            "title=",  # 標題屬性
            "role=",  # ARIA 角色
        ]
        
        # 至少應該有一些無障礙標記
        accessibility_score = sum(1 for indicator in accessibility_indicators if indicator in content)
        assert accessibility_score >= 1, "頁面缺少基本的無障礙標記"
        
        # 測試鍵盤導航友好的搜尋
        simple_search = {
            "job_title": "accessible design",
            "location": "usa",
            "results_wanted": 10
        }
        
        search_response = accessibility_session.post(f"{self.BASE_URL}/search", data=simple_search)
        assert search_response.status_code in [200, 400, 422]
        
        accessibility_session.close()
    
    def teardown_method(self):
        """測試後清理"""
        if hasattr(self, 'session'):
            self.session.close()


if __name__ == "__main__":
    # 可以直接運行此檔案進行測試
    pytest.main([__file__, "-v"])