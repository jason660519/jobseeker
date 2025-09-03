#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行增強版爬蟲
使用替代搜尋策略，直接訪問搜尋URL避免彈出視窗問題
"""

import asyncio
import json
import urllib.parse
import time
import random
from datetime import datetime
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from .constant import BASE_URL, SEARCH_URL, USER_AGENTS, ANT_DETECTION_CONFIG


class EnhancedTW104Scraper:
    """104人力銀行增強版爬蟲"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.base_url = BASE_URL
        self.search_base_url = SEARCH_URL
        self.user_agents = USER_AGENTS
        self.anti_detection_config = ANT_DETECTION_CONFIG
        
        # 搜尋結果存儲
        self.job_results = []
        self.search_metadata = {}
        
    async def search_jobs(
        self, 
        keyword: str, 
        location: Optional[str] = None,
        job_category: Optional[str] = None,
        max_pages: int = 5,
        delay_range: tuple = (1, 3)
    ) -> List[Dict[str, Any]]:
        """
        搜尋職位
        
        Args:
            keyword: 搜尋關鍵字
            location: 地區代碼 (可選)
            job_category: 職務類別代碼 (可選)
            max_pages: 最大搜尋頁數
            delay_range: 請求間隔範圍 (秒)
            
        Returns:
            職位列表
        """
        print(f"🔍 開始搜尋104人力銀行職位: {keyword}")
        
        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p)
                context = await self._create_context(browser)
                page = await context.new_page()
                
                # 搜尋所有頁面
                all_jobs = []
                for page_num in range(1, max_pages + 1):
                    print(f"📄 搜尋第 {page_num} 頁...")
                    
                    # 構建搜尋URL
                    search_url = self._build_search_url(
                        keyword, location, job_category, page_num
                    )
                    
                    # 搜尋當前頁面
                    page_jobs = await self._search_single_page(page, search_url)
                    
                    if not page_jobs:
                        print(f"⚠️  第 {page_num} 頁沒有找到職位，停止搜尋")
                        break
                    
                    all_jobs.extend(page_jobs)
                    print(f"✅ 第 {page_num} 頁找到 {len(page_jobs)} 個職位")
                    
                    # 隨機延遲
                    if page_num < max_pages:
                        delay = random.uniform(*delay_range)
                        print(f"⏳ 等待 {delay:.1f} 秒...")
                        await asyncio.sleep(delay)
                
                await browser.close()
                
                # 保存結果
                self.job_results = all_jobs
                self.search_metadata = {
                    "keyword": keyword,
                    "location": location,
                    "job_category": job_category,
                    "total_jobs": len(all_jobs),
                    "search_time": datetime.now().isoformat()
                }
                
                print(f"🎉 搜尋完成！總共找到 {len(all_jobs)} 個職位")
                return all_jobs
                
        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")
            return []
    
    async def _launch_browser(self, playwright) -> Browser:
        """啟動瀏覽器"""
        return await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-popup-blocking',
                '--disable-notifications',
                '--disable-extensions',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--no-default-browser-check'
            ]
        )
    
    async def _create_context(self, browser: Browser) -> BrowserContext:
        """創建瀏覽器上下文"""
        user_agent = random.choice(self.user_agents)
        
        return await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='zh-TW',
            timezone_id='Asia/Taipei',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
    
    def _build_search_url(
        self, 
        keyword: str, 
        location: Optional[str] = None,
        job_category: Optional[str] = None,
        page: int = 1
    ) -> str:
        """構建搜尋URL"""
        params = {
            'keyword': keyword,
            'order': '1',  # 相關性排序
            'asc': '0',    # 降序
            'page': str(page)
        }
        
        if location:
            params['area'] = location
        
        if job_category:
            params['jobcat'] = job_category
        
        query_string = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return f"{self.search_base_url}?{query_string}"
    
    async def _search_single_page(self, page: Page, search_url: str) -> List[Dict[str, Any]]:
        """搜尋單一頁面"""
        try:
            # 訪問搜尋頁面
            await page.goto(search_url, timeout=self.timeout)
            await page.wait_for_load_state('networkidle')
            
            # 等待職位列表載入
            await page.wait_for_selector('.job-list', timeout=10000)
            
            # 提取職位資訊
            jobs = await self._extract_job_info(page)
            
            return jobs
            
        except Exception as e:
            print(f"❌ 搜尋頁面失敗: {e}")
            return []
    
    async def _extract_job_info(self, page: Page) -> List[Dict[str, Any]]:
        """提取職位資訊"""
        try:
            # 等待職位元素載入
            await page.wait_for_selector('.job', timeout=5000)
            
            # 提取職位資訊
            jobs = await page.evaluate("""
                () => {
                    const jobElements = document.querySelectorAll('.job');
                    const jobs = [];
                    
                    jobElements.forEach((element, index) => {
                        try {
                            // 獲取完整文本內容
                            const fullText = element.textContent || '';
                            
                            // 職位標題 - 從完整文本中提取
                            let title = '';
                            let jobUrl = '';
                            
                            // 嘗試從鏈接中獲取標題
                            const titleLink = element.querySelector('a[href*="/job/"]');
                            if (titleLink) {
                                title = titleLink.textContent.trim();
                                jobUrl = titleLink.href;
                            } else {
                                // 如果沒有鏈接，嘗試從文本中提取標題
                                const lines = fullText.split('\\n').map(line => line.trim()).filter(line => line);
                                if (lines.length > 0) {
                                    title = lines[0];
                                }
                            }
                            
                            // 公司名稱 - 從文本中提取
                            let company = '';
                            let companyUrl = '';
                            
                            // 嘗試從鏈接中獲取公司名稱
                            const companyLink = element.querySelector('a[href*="/company/"]');
                            if (companyLink) {
                                company = companyLink.textContent.trim();
                                companyUrl = companyLink.href;
                            } else {
                                // 從文本中提取公司名稱（通常在第二行）
                                const lines = fullText.split('\\n').map(line => line.trim()).filter(line => line);
                                if (lines.length > 1) {
                                    company = lines[1];
                                }
                            }
                            
                            // 工作地點 - 從文本中提取
                            let location = '';
                            const locationMatch = fullText.match(/台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義縣|屏東縣|宜蘭縣|花蓮縣|台東縣|澎湖縣|金門縣|連江縣/);
                            if (locationMatch) {
                                location = locationMatch[0];
                            }
                            
                            // 薪資 - 從文本中提取
                            let salary = '';
                            const salaryMatch = fullText.match(/\\$[0-9,]+|面議|待遇面議|薪資面議|月薪[0-9,]+|年薪[0-9,]+/);
                            if (salaryMatch) {
                                salary = salaryMatch[0];
                            }
                            
                            // 工作經驗 - 從文本中提取
                            let experience = '';
                            const expMatch = fullText.match(/[0-9]+年以上|[0-9]+年以下|無經驗|1年以下|2年以下|3年以下|4年以下|5年以下|6年以下|7年以下|8年以下|9年以下|10年以下/);
                            if (expMatch) {
                                experience = expMatch[0];
                            }
                            
                            // 學歷要求 - 從文本中提取
                            let education = '';
                            const eduMatch = fullText.match(/大學|碩士|博士|專科|高中|國中|不拘|不限/);
                            if (eduMatch) {
                                education = eduMatch[0];
                            }
                            
                            // 發布時間 - 從文本中提取
                            let publishTime = '';
                            const timeMatch = fullText.match(/[0-9]+天前|[0-9]+小時前|[0-9]+分鐘前|今天|昨天|本週|上週/);
                            if (timeMatch) {
                                publishTime = timeMatch[0];
                            }
                            
                            // 職位ID
                            const jobId = jobUrl ? jobUrl.split('/').pop() : '';
                            
                            // 職位描述 - 取完整文本的前200個字符
                            const description = fullText.length > 200 ? fullText.substring(0, 200) + '...' : fullText;
                            
                            if (title && company) {
                                jobs.push({
                                    job_id: jobId,
                                    title: title,
                                    company: company,
                                    location: location,
                                    salary: salary,
                                    experience: experience,
                                    education: education,
                                    description: description,
                                    publish_time: publishTime,
                                    job_url: jobUrl,
                                    company_url: companyUrl,
                                    scraped_at: new Date().toISOString()
                                });
                            }
                        } catch (error) {
                            console.error('Error extracting job info:', error);
                        }
                    });
                    
                    return jobs;
                }
            """)
            
            return jobs
            
        except Exception as e:
            print(f"❌ 提取職位資訊失敗: {e}")
            return []
    
    async def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """獲取職位詳細資訊"""
        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p)
                context = await self._create_context(browser)
                page = await context.new_page()
                
                await page.goto(job_url, timeout=self.timeout)
                await page.wait_for_load_state('networkidle')
                
                # 提取詳細資訊
                details = await page.evaluate("""
                    () => {
                        const details = {};
                        
                        // 職位描述
                        const descriptionElement = document.querySelector('.job-description, .job-content, .content');
                        details.description = descriptionElement ? descriptionElement.textContent.trim() : '';
                        
                        // 工作內容
                        const contentElement = document.querySelector('.job-content, .work-content, .content');
                        details.work_content = contentElement ? contentElement.textContent.trim() : '';
                        
                        // 職位要求
                        const requirementsElement = document.querySelector('.job-requirements, .requirements, .qualifications');
                        details.requirements = requirementsElement ? requirementsElement.textContent.trim() : '';
                        
                        // 公司資訊
                        const companyInfoElement = document.querySelector('.company-info, .company-details');
                        details.company_info = companyInfoElement ? companyInfoElement.textContent.trim() : '';
                        
                        // 福利待遇
                        const benefitsElement = document.querySelector('.job-benefits, .benefits, .welfare');
                        details.benefits = benefitsElement ? benefitsElement.textContent.trim() : '';
                        
                        return details;
                    }
                """)
                
                await browser.close()
                return details
                
        except Exception as e:
            print(f"❌ 獲取職位詳細資訊失敗: {e}")
            return {}
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """保存搜尋結果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tw104_jobs_{timestamp}.json"
        
        filepath = f"tests/results/{filename}"
        
        data = {
            "metadata": self.search_metadata,
            "jobs": self.job_results,
            "total_count": len(self.job_results),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 搜尋結果已保存至: {filepath}")
        return filepath
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取搜尋統計資訊"""
        if not self.job_results:
            return {"error": "沒有搜尋結果"}
        
        # 統計公司
        companies = [job.get('company', '') for job in self.job_results if job.get('company')]
        company_count = len(set(companies))
        
        # 統計地區
        locations = [job.get('location', '') for job in self.job_results if job.get('location')]
        location_count = len(set(locations))
        
        # 統計薪資範圍
        salaries = [job.get('salary', '') for job in self.job_results if job.get('salary')]
        salary_count = len([s for s in salaries if s])
        
        return {
            "total_jobs": len(self.job_results),
            "unique_companies": company_count,
            "unique_locations": location_count,
            "jobs_with_salary": salary_count,
            "search_metadata": self.search_metadata
        }


# 使用範例
async def main():
    """使用範例"""
    scraper = EnhancedTW104Scraper(headless=True)
    
    # 搜尋職位
    jobs = await scraper.search_jobs(
        keyword="Python工程師",
        location="6001001000",  # 台北市
        max_pages=3
    )
    
    # 顯示統計資訊
    stats = scraper.get_statistics()
    print(f"📊 搜尋統計: {stats}")
    
    # 保存結果
    scraper.save_results()


if __name__ == "__main__":
    asyncio.run(main())
