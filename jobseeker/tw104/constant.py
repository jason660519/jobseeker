#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
104人力銀行爬蟲常數配置
"""

# 104人力銀行基本URL
BASE_URL = "https://www.104.com.tw"
SEARCH_URL = "https://www.104.com.tw/jobs/search/"

# 用戶代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

# 反偵測配置
ANT_DETECTION_CONFIG = {
    "viewport": {"width": 1920, "height": 1080},
    "user_agent_rotation": True,
    "random_delay": True,
    "delay_range": (1, 3),
    "stealth_mode": True
}

# 搜尋參數配置
SEARCH_CONFIG = {
    "default_order": "1",  # 相關性排序
    "default_asc": "0",    # 降序
    "max_pages": 10,
    "timeout": 30000
}

# 地區代碼
AREA_CODES = {
    "台北市": "6001001000",
    "新北市": "6001002000", 
    "桃園市": "6001003000",
    "台中市": "6001004000",
    "台南市": "6001005000",
    "高雄市": "6001006000",
    "基隆市": "6001007000",
    "新竹市": "6001008000",
    "嘉義市": "6001009000",
    "新竹縣": "6001010000",
    "苗栗縣": "6001011000",
    "彰化縣": "6001012000",
    "南投縣": "6001013000",
    "雲林縣": "6001014000",
    "嘉義縣": "6001015000",
    "屏東縣": "6001016000",
    "宜蘭縣": "6001017000",
    "花蓮縣": "6001018000",
    "台東縣": "6001019000",
    "澎湖縣": "6001020000",
    "金門縣": "6001021000",
    "連江縣": "6001022000"
}

# 職務類別代碼
JOB_CATEGORY_CODES = {
    "軟體工程師": "2007000000",
    "系統工程師": "2007001000",
    "網路工程師": "2007002000",
    "資料庫管理師": "2007003000",
    "資訊安全工程師": "2007004000",
    "前端工程師": "2007005000",
    "後端工程師": "2007006000",
    "全端工程師": "2007007000",
    "行動應用工程師": "2007008000",
    "遊戲程式設計師": "2007009000",
    "演算法工程師": "2007010000",
    "人工智慧工程師": "2007011000",
    "資料科學家": "2007012000",
    "資料分析師": "2007013000",
    "產品經理": "2008000000",
    "專案經理": "2008001000",
    "UI設計師": "2009000000",
    "UX設計師": "2009001000",
    "平面設計師": "2009002000",
    "網頁設計師": "2009003000"
}

# 選擇器配置
SELECTORS = {
    "job_list": ".job-list",
    "job_item": ".job-list > div",
    "job_title": ".job-list-item-title a, .job-title a, h3 a",
    "company_name": ".job-list-item-company a, .company-name a, .company a",
    "job_location": ".job-list-item-area, .job-area, .location",
    "job_salary": ".job-list-item-salary, .job-salary, .salary",
    "job_experience": ".job-list-item-experience, .job-experience, .experience",
    "job_education": ".job-list-item-education, .job-education, .education",
    "job_description": ".job-list-item-description, .job-description, .description",
    "job_time": ".job-list-item-time, .job-time, .time",
    "pagination": ".pagination",
    "next_page": ".pagination .next, .pagination .page-next"
}

# 錯誤處理配置
ERROR_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,
    "timeout": 30000,
    "ignore_errors": [
        "TimeoutError",
        "NetworkError",
        "ElementNotFound"
    ]
}
