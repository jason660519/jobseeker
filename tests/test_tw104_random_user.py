#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行爬蟲隨機用戶測試腳本
模擬真實用戶行為，測試爬蟲的穩定性和反檢測能力
"""

import pytest
import asyncio
import time
import random
import string
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Playwright 導入
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.sync_api import sync_playwright

# 測試工具導入
from tests.fixtures.test_utils import (
    MockHTTPResponse, MockScraper, create_mock_job_data,
    measure_execution_time, NetworkDelaySimulator,
    PerformanceMonitor, monitor_system_resources
)
from tests.fixtures.test_data import (
    SAMPLE_JOB_DATA, SEARCH_PARAMETERS, SITE_SPECIFIC_DATA,
    MOCK_RESPONSES, get_sample_jobs
)


class RandomUserSimulator:
    """隨機用戶行為模擬器"""
    
    def __init__(self):
        self.user_profiles = self._generate_user_profiles()
        self.search_patterns = self._generate_search_patterns()
        self.behavior_patterns = self._generate_behavior_patterns()
    
    def _generate_user_profiles(self) -> List[Dict[str, Any]]:
        """生成隨機用戶檔案"""
        profiles = []
        
        # 不同類型的用戶
        user_types = [
            {
                "type": "fresh_graduate",
                "search_terms": ["助理", "實習", "junior", "entry level", "新人"],
                "locations": ["台北", "新北", "桃園", "台中", "高雄"],
                "job_types": ["fulltime", "internship"],
                "experience_level": "entry"
            },
            {
                "type": "experienced_professional",
                "search_terms": ["資深", "senior", "manager", "lead", "主管"],
                "locations": ["台北", "新北", "桃園", "台中", "高雄", "新竹"],
                "job_types": ["fulltime", "contract"],
                "experience_level": "senior"
            },
            {
                "type": "career_changer",
                "search_terms": ["轉職", "career change", "跨領域", "學習"],
                "locations": ["台北", "新北", "台中", "高雄"],
                "job_types": ["fulltime", "parttime"],
                "experience_level": "mid"
            },
            {
                "type": "remote_worker",
                "search_terms": ["遠端", "remote", "在家工作", "WFH"],
                "locations": ["全台", "remote", "不限地區"],
                "job_types": ["fulltime", "contract", "parttime"],
                "experience_level": "any"
            }
        ]
        
        for user_type in user_types:
            for i in range(5):  # 每種類型生成5個用戶
                profile = {
                    "id": f"{user_type['type']}_{i+1}",
                    "type": user_type["type"],
                    "search_terms": random.sample(user_type["search_terms"], 
                                                min(3, len(user_type["search_terms"]))),
                    "locations": random.sample(user_type["locations"], 
                                             min(2, len(user_type["locations"]))),
                    "job_types": user_type["job_types"],
                    "experience_level": user_type["experience_level"],
                    "search_frequency": random.uniform(0.5, 3.0),  # 搜尋間隔（秒）
                    "page_views": random.randint(3, 15),  # 每次搜尋瀏覽頁數
                    "click_probability": random.uniform(0.3, 0.8),  # 點擊機率
                    "session_duration": random.uniform(300, 1800)  # 會話時長（秒）
                }
                profiles.append(profile)
        
        return profiles
    
    def _generate_search_patterns(self) -> List[Dict[str, Any]]:
        """生成搜尋模式"""
        return [
            {
                "pattern": "broad_search",
                "search_terms": ["工程師", "developer", "programmer", "軟體"],
                "locations": ["台北", "新北", "桃園"],
                "results_wanted": random.randint(20, 50)
            },
            {
                "pattern": "specific_search", 
                "search_terms": ["Python工程師", "React開發", "DevOps工程師"],
                "locations": ["台北", "新竹"],
                "results_wanted": random.randint(10, 30)
            },
            {
                "pattern": "location_focused",
                "search_terms": ["工程師", "設計師", "行銷"],
                "locations": ["台中", "高雄", "台南"],
                "results_wanted": random.randint(15, 40)
            },
            {
                "pattern": "skill_focused",
                "search_terms": ["AI", "機器學習", "區塊鏈", "雲端"],
                "locations": ["台北", "新竹", "台中"],
                "results_wanted": random.randint(5, 25)
            }
        ]
    
    def _generate_behavior_patterns(self) -> List[Dict[str, Any]]:
        """生成行為模式"""
        return [
            {
                "name": "quick_browser",
                "page_load_delay": (0.5, 2.0),
                "scroll_speed": "fast",
                "click_delay": (0.1, 0.5),
                "session_style": "efficient"
            },
            {
                "name": "thorough_researcher",
                "page_load_delay": (2.0, 5.0),
                "scroll_speed": "slow",
                "click_delay": (1.0, 3.0),
                "session_style": "detailed"
            },
            {
                "name": "casual_browser",
                "page_load_delay": (1.0, 3.0),
                "scroll_speed": "medium",
                "click_delay": (0.5, 2.0),
                "session_style": "relaxed"
            },
            {
                "name": "mobile_user",
                "page_load_delay": (1.5, 4.0),
                "scroll_speed": "medium",
                "click_delay": (0.3, 1.5),
                "session_style": "mobile"
            }
        ]
    
    def get_random_user(self) -> Dict[str, Any]:
        """獲取隨機用戶"""
        return random.choice(self.user_profiles)
    
    def get_random_search_pattern(self) -> Dict[str, Any]:
        """獲取隨機搜尋模式"""
        return random.choice(self.search_patterns)
    
    def get_random_behavior(self) -> Dict[str, Any]:
        """獲取隨機行為模式"""
        return random.choice(self.behavior_patterns)


class TW104RandomUserTest:
    """104人力銀行隨機用戶測試類"""
    
    def __init__(self):
        self.simulator = RandomUserSimulator()
        self.performance_monitor = PerformanceMonitor()
        self.test_results = []
        self.base_url = "https://www.104.com.tw"
    
    async def simulate_user_session(self, user_profile: Dict[str, Any], 
                                  behavior_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """模擬用戶會話"""
        session_result = {
            "user_id": user_profile["id"],
            "user_type": user_profile["type"],
            "behavior_pattern": behavior_pattern["name"],
            "start_time": datetime.now(),
            "actions": [],
            "errors": [],
            "performance_metrics": {}
        }
        
        try:
            async with async_playwright() as p:
                # 啟動瀏覽器
                browser = await p.chromium.launch(
                    headless=True,  # 無頭模式，提高測試速度
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # 創建上下文，模擬真實用戶
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='zh-TW',
                    timezone_id='Asia/Taipei'
                )
                
                page = await context.new_page()
                
                # 開始性能監控
                self.performance_monitor.start_monitoring()
                
                # 模擬用戶行為
                await self._simulate_user_behavior(page, user_profile, behavior_pattern, session_result)
                
                # 停止性能監控
                self.performance_monitor.stop_monitoring()
                session_result["performance_metrics"] = self.performance_monitor.get_summary()
                
                await browser.close()
                
        except Exception as e:
            session_result["errors"].append({
                "type": "session_error",
                "message": str(e),
                "timestamp": datetime.now()
            })
        
        session_result["end_time"] = datetime.now()
        session_result["duration"] = (session_result["end_time"] - session_result["start_time"]).total_seconds()
        
        return session_result
    
    async def _simulate_user_behavior(self, page: Page, user_profile: Dict[str, Any],
                                    behavior_pattern: Dict[str, Any], 
                                    session_result: Dict[str, Any]):
        """模擬用戶行為"""
        
        # 1. 訪問首頁
        await self._visit_homepage(page, behavior_pattern, session_result)
        
        # 2. 執行多次搜尋
        search_count = random.randint(2, 5)
        for i in range(search_count):
            await self._perform_search(page, user_profile, behavior_pattern, session_result)
            
            # 搜尋間隔
            delay = random.uniform(*behavior_pattern["page_load_delay"])
            await asyncio.sleep(delay)
        
        # 3. 模擬瀏覽行為
        await self._simulate_browsing(page, user_profile, behavior_pattern, session_result)
    
    async def _visit_homepage(self, page: Page, behavior_pattern: Dict[str, Any],
                            session_result: Dict[str, Any]):
        """訪問首頁"""
        try:
            action = {
                "type": "visit_homepage",
                "timestamp": datetime.now(),
                "url": self.base_url
            }
            
            await page.goto(self.base_url, wait_until='networkidle', timeout=30000)
            
            # 模擬用戶閱讀時間
            read_time = random.uniform(2.0, 8.0)
            await asyncio.sleep(read_time)
            
            # 模擬滾動
            await self._simulate_scrolling(page, behavior_pattern)
            
            action["success"] = True
            action["duration"] = read_time
            
        except Exception as e:
            action["success"] = False
            action["error"] = str(e)
            session_result["errors"].append(action)
        
        session_result["actions"].append(action)
    
    async def _perform_search(self, page: Page, user_profile: Dict[str, Any],
                            behavior_pattern: Dict[str, Any], 
                            session_result: Dict[str, Any]):
        """執行搜尋"""
        try:
            # 選擇搜尋詞和地點
            search_term = random.choice(user_profile["search_terms"])
            location = random.choice(user_profile["locations"])
            
            action = {
                "type": "search",
                "timestamp": datetime.now(),
                "search_term": search_term,
                "location": location
            }
            
            # 嘗試多種搜尋輸入選擇器
            search_selectors = [
                'input[name="keyword"]',
                'input[placeholder*="職務"]',
                'input[placeholder*="工作"]',
                '#keyword',
                '.search-input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = page.locator(selector)
                    if await search_input.count() > 0:
                        break
                except:
                    continue
            
            if search_input and await search_input.count() > 0:
                await search_input.fill("")
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # 模擬逐字輸入
                for char in search_term:
                    await search_input.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.2))
                
                # 嘗試點擊搜尋按鈕
                search_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("搜尋")',
                    '.search-btn',
                    '#search-btn'
                ]
                
                search_clicked = False
                for selector in search_button_selectors:
                    try:
                        search_button = page.locator(selector)
                        if await search_button.count() > 0:
                            await search_button.click()
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            search_clicked = True
                            break
                    except:
                        continue
                
                if search_clicked:
                    # 模擬瀏覽結果
                    await self._browse_search_results(page, behavior_pattern, session_result)
                    action["success"] = True
                else:
                    action["success"] = False
                    action["error"] = "Search button not found"
            else:
                action["success"] = False
                action["error"] = "Search input not found"
            
        except Exception as e:
            action["success"] = False
            action["error"] = str(e)
            session_result["errors"].append(action)
        
        session_result["actions"].append(action)
    
    async def _browse_search_results(self, page: Page, behavior_pattern: Dict[str, Any],
                                   session_result: Dict[str, Any]):
        """瀏覽搜尋結果"""
        try:
            # 等待結果載入，嘗試多種結果選擇器
            result_selectors = [
                '.job-list-item',
                '.job-item',
                '.job-card',
                '[data-testid="job-item"]',
                '.job'
            ]
            
            result_loaded = False
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    result_loaded = True
                    break
                except:
                    continue
            
            if result_loaded:
                # 模擬滾動瀏覽
                await self._simulate_scrolling(page, behavior_pattern)
                
                # 模擬點擊職位
                job_items = page.locator('.job-list-item, .job-item, .job-card')
                job_count = await job_items.count()
                
                if job_count > 0:
                    # 隨機點擊幾個職位
                    click_count = min(random.randint(1, 3), job_count)
                    for i in range(click_count):
                        if random.random() < behavior_pattern.get("click_probability", 0.5):
                            try:
                                job_item = job_items.nth(random.randint(0, job_count - 1))
                                await job_item.click()
                                await asyncio.sleep(random.uniform(1.0, 3.0))
                                
                                # 返回結果頁面
                                await page.go_back()
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                
                            except Exception as e:
                                session_result["errors"].append({
                                    "type": "click_error",
                                    "message": str(e),
                                    "timestamp": datetime.now()
                                })
            
        except Exception as e:
            session_result["errors"].append({
                "type": "browse_error",
                "message": str(e),
                "timestamp": datetime.now()
            })
    
    async def _simulate_scrolling(self, page: Page, behavior_pattern: Dict[str, Any]):
        """模擬滾動行為"""
        scroll_speed = behavior_pattern.get("scroll_speed", "medium")
        
        if scroll_speed == "fast":
            scroll_delay = (0.1, 0.3)
            scroll_amount = 500
        elif scroll_speed == "slow":
            scroll_delay = (0.5, 1.5)
            scroll_amount = 200
        else:  # medium
            scroll_delay = (0.2, 0.8)
            scroll_amount = 300
        
        # 模擬多次滾動
        scroll_count = random.randint(3, 8)
        for _ in range(scroll_count):
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(*scroll_delay))
    
    async def _simulate_browsing(self, page: Page, user_profile: Dict[str, Any],
                               behavior_pattern: Dict[str, Any], 
                               session_result: Dict[str, Any]):
        """模擬瀏覽行為"""
        try:
            # 模擬瀏覽不同頁面
            pages_to_visit = [
                "/jobs/search/",
                "/jobs/category/",
                "/companies/"
            ]
            
            for page_path in random.sample(pages_to_visit, random.randint(1, 2)):
                try:
                    await page.goto(f"{self.base_url}{page_path}", timeout=30000)
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # 模擬瀏覽時間
                    browse_time = random.uniform(3.0, 10.0)
                    await asyncio.sleep(browse_time)
                    
                    # 模擬滾動
                    await self._simulate_scrolling(page, behavior_pattern)
                    
                except Exception as e:
                    session_result["errors"].append({
                        "type": "page_browse_error",
                        "page": page_path,
                        "message": str(e),
                        "timestamp": datetime.now()
                    })
        
        except Exception as e:
            session_result["errors"].append({
                "type": "browsing_error",
                "message": str(e),
                "timestamp": datetime.now()
            })


class TestTW104RandomUser:
    """104人力銀行隨機用戶測試類"""
    
    @pytest.fixture(scope="class")
    def test_runner(self):
        """測試運行器"""
        return TW104RandomUserTest()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.requires_network
    async def test_single_random_user_session(self, test_runner):
        """測試單個隨機用戶會話"""
        user_profile = test_runner.simulator.get_random_user()
        behavior_pattern = test_runner.simulator.get_random_behavior()
        
        session_result = await test_runner.simulate_user_session(user_profile, behavior_pattern)
        
        # 驗證會話結果
        assert session_result["user_id"] is not None
        assert session_result["duration"] > 0
        assert len(session_result["actions"]) > 0
        
        # 檢查是否有嚴重錯誤
        critical_errors = [e for e in session_result["errors"] 
                          if e["type"] in ["session_error", "critical_error"]]
        assert len(critical_errors) == 0, f"Critical errors found: {critical_errors}"
        
        # 記錄測試結果
        test_runner.test_results.append(session_result)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.requires_network
    async def test_multiple_user_sessions(self, test_runner):
        """測試多個用戶會話"""
        session_count = 3  # 測試3個不同的用戶會話
        
        for i in range(session_count):
            user_profile = test_runner.simulator.get_random_user()
            behavior_pattern = test_runner.simulator.get_random_behavior()
            
            session_result = await test_runner.simulate_user_session(user_profile, behavior_pattern)
            
            # 基本驗證
            assert session_result["user_id"] is not None
            assert session_result["duration"] > 0
            
            # 記錄結果
            test_runner.test_results.append(session_result)
            
            # 會話間隔
            await asyncio.sleep(random.uniform(5.0, 15.0))
        
        # 驗證所有會話都成功
        assert len(test_runner.test_results) == session_count
        
        # 檢查整體成功率
        successful_sessions = [r for r in test_runner.test_results 
                              if len([e for e in r["errors"] 
                                    if e["type"] in ["session_error", "critical_error"]]) == 0]
        
        success_rate = len(successful_sessions) / len(test_runner.test_results)
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.2%}"
    
    def test_generate_test_report(self, test_runner):
        """生成測試報告"""
        if not test_runner.test_results:
            pytest.skip("No test results to report")
        
        # 生成測試報告
        report = {
            "test_summary": {
                "total_sessions": len(test_runner.test_results),
                "successful_sessions": len([r for r in test_runner.test_results 
                                          if len([e for e in r["errors"] 
                                                if e["type"] in ["session_error", "critical_error"]]) == 0]),
                "total_errors": sum(len(r["errors"]) for r in test_runner.test_results),
                "avg_session_duration": sum(r["duration"] for r in test_runner.test_results) / len(test_runner.test_results)
            },
            "user_type_analysis": {},
            "behavior_pattern_analysis": {},
            "error_analysis": {},
            "performance_analysis": {}
        }
        
        # 分析用戶類型
        for result in test_runner.test_results:
            user_type = result["user_type"]
            if user_type not in report["user_type_analysis"]:
                report["user_type_analysis"][user_type] = {"count": 0, "avg_duration": 0, "errors": 0}
            
            report["user_type_analysis"][user_type]["count"] += 1
            report["user_type_analysis"][user_type]["avg_duration"] += result["duration"]
            report["user_type_analysis"][user_type]["errors"] += len(result["errors"])
        
        # 計算平均值
        for user_type, data in report["user_type_analysis"].items():
            data["avg_duration"] /= data["count"]
        
        # 分析行為模式
        for result in test_runner.test_results:
            behavior = result["behavior_pattern"]
            if behavior not in report["behavior_pattern_analysis"]:
                report["behavior_pattern_analysis"][behavior] = {"count": 0, "avg_duration": 0}
            
            report["behavior_pattern_analysis"][behavior]["count"] += 1
            report["behavior_pattern_analysis"][behavior]["avg_duration"] += result["duration"]
        
        # 計算平均值
        for behavior, data in report["behavior_pattern_analysis"].items():
            data["avg_duration"] /= data["count"]
        
        # 分析錯誤
        all_errors = []
        for result in test_runner.test_results:
            all_errors.extend(result["errors"])
        
        error_types = {}
        for error in all_errors:
            error_type = error["type"]
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        report["error_analysis"] = error_types
        
        # 分析性能
        performance_metrics = []
        for result in test_runner.test_results:
            if "performance_metrics" in result and result["performance_metrics"]:
                performance_metrics.append(result["performance_metrics"])
        
        if performance_metrics:
            report["performance_analysis"] = {
                "avg_memory_mb": sum(m.get("avg_memory_mb", 0) for m in performance_metrics) / len(performance_metrics),
                "max_memory_mb": max(m.get("max_memory_mb", 0) for m in performance_metrics),
                "avg_cpu_percent": sum(m.get("avg_cpu_percent", 0) for m in performance_metrics) / len(performance_metrics),
                "max_cpu_percent": max(m.get("max_cpu_percent", 0) for m in performance_metrics)
            }
        
        # 保存報告
        report_path = Path("tests/results/tw104_random_user_test_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n=== 104人力銀行隨機用戶測試報告 ===")
        print(f"總會話數: {report['test_summary']['total_sessions']}")
        print(f"成功會話數: {report['test_summary']['successful_sessions']}")
        print(f"成功率: {report['test_summary']['successful_sessions']/report['test_summary']['total_sessions']:.2%}")
        print(f"平均會話時長: {report['test_summary']['avg_session_duration']:.2f}秒")
        print(f"總錯誤數: {report['test_summary']['total_errors']}")
        
        if report["performance_analysis"]:
            print(f"\n=== 性能分析 ===")
            print(f"平均記憶體使用: {report['performance_analysis']['avg_memory_mb']:.2f}MB")
            print(f"最大記憶體使用: {report['performance_analysis']['max_memory_mb']:.2f}MB")
            print(f"平均CPU使用: {report['performance_analysis']['avg_cpu_percent']:.2f}%")
            print(f"最大CPU使用: {report['performance_analysis']['max_cpu_percent']:.2f}%")
        
        print(f"\n詳細報告已保存至: {report_path}")


# 輔助函數
def generate_random_search_terms() -> List[str]:
    """生成隨機搜尋詞"""
    tech_terms = ["Python", "Java", "JavaScript", "React", "Vue", "Node.js", "Django", "Flask"]
    job_titles = ["工程師", "開發者", "設計師", "分析師", "專案經理", "產品經理"]
    experience_levels = ["資深", "中級", "初級", "實習", "主管", "Lead"]
    
    terms = []
    for _ in range(random.randint(1, 3)):
        if random.random() < 0.5:
            term = random.choice(tech_terms)
        else:
            term = random.choice(job_titles)
        
        if random.random() < 0.3:
            term = f"{random.choice(experience_levels)}{term}"
        
        terms.append(term)
    
    return terms


def generate_random_locations() -> List[str]:
    """生成隨機地點"""
    locations = ["台北", "新北", "桃園", "台中", "高雄", "新竹", "台南", "基隆", "宜蘭", "花蓮"]
    return random.sample(locations, random.randint(1, 3))


if __name__ == "__main__":
    # 可以直接運行此檔案進行測試
    pytest.main([__file__, "-v", "-s"])
