#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的TW104職位提取測試
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def test_simple_extraction():
    """簡單的職位提取測試"""
    print("🔍 開始簡單的職位提取測試...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # 訪問搜尋頁面
            search_url = "https://www.104.com.tw/jobs/search/?keyword=Python工程師"
            print(f"📄 訪問: {search_url}")
            
            await page.goto(search_url, timeout=60000)
            await page.wait_for_load_state('networkidle')
            
            # 等待職位列表載入
            await page.wait_for_selector('.job-list > div', timeout=10000)
            
            # 提取職位資訊
            jobs = await page.evaluate("""
                () => {
                    const jobElements = document.querySelectorAll('.job-list > div');
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
                                    description: description,
                                    job_url: jobUrl,
                                    company_url: companyUrl
                                });
                            }
                        } catch (error) {
                            console.error('Error extracting job info:', error);
                        }
                    });
                    
                    return jobs;
                }
            """)
            
            print(f"📊 找到 {len(jobs)} 個職位")
            
            # 顯示前3個職位
            for i, job in enumerate(jobs[:3]):
                print(f"\n職位 {i+1}:")
                print(f"  標題: {job.get('title', 'N/A')}")
                print(f"  公司: {job.get('company', 'N/A')}")
                print(f"  地點: {job.get('location', 'N/A')}")
                print(f"  薪資: {job.get('salary', 'N/A')}")
                print(f"  URL: {job.get('job_url', 'N/A')}")
            
            await browser.close()
            
            # 保存結果
            with open('tests/results/simple_extraction_test.json', 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 結果已保存至: tests/results/simple_extraction_test.json")
            
            return len(jobs) > 0
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_extraction())
    print(f"\n{'='*50}")
    print(f"測試結果: {'✅ 成功' if success else '❌ 失敗'}")
    print(f"{'='*50}")
