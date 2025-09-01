"""Seek.com.au 常數定義

此模塊包含 Seek 爬蟲所需的常數和配置信息。
"""

# Seek 網站基礎 URL
BASE_URL = "https://www.seek.com.au"
JOBS_URL = f"{BASE_URL}/jobs"

# 工作類型映射
JOB_TYPE_MAPPING = {
    "full-time": "242",
    "part-time": "243",
    "contract": "244",
    "casual": "245",
    "internship": "7"
}

# 澳洲州份映射
STATE_MAPPING = {
    "NSW": "New South Wales",
    "VIC": "Victoria", 
    "QLD": "Queensland",
    "WA": "Western Australia",
    "SA": "South Australia",
    "TAS": "Tasmania",
    "ACT": "Australian Capital Territory",
    "NT": "Northern Territory"
}

# 薪資間隔映射
SALARY_INTERVAL_MAPPING = {
    "hourly": "HOURLY",
    "daily": "DAILY", 
    "weekly": "WEEKLY",
    "monthly": "MONTHLY",
    "yearly": "YEARLY",
    "per hour": "HOURLY",
    "per day": "DAILY",
    "per week": "WEEKLY", 
    "per month": "MONTHLY",
    "per year": "YEARLY",
    "per annum": "YEARLY"
}

# 請求頭配置
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

# 用戶代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

# 搜索參數
SEARCH_PARAMS = {
    "q": None,          # 搜索關鍵詞
    "where": None,      # 地點
    "page": 1,          # 頁碼
    "worktype": None,   # 工作類型
    "workfromhome": None # 遠程工作
}

# 延遲配置（秒）
DELAYS = {
    'between_requests': (1.0, 3.0),
    'between_pages': (2.0, 5.0),
    'page_load': (2.0, 4.0)
}

# 重試配置
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2.0,
    'backoff_factor': 1.5
}

# 超時配置（秒）
TIMEOUT_CONFIG = {
    'request': 30,
    'page_load': 60,
    'element_wait': 10
}

# 分頁配置
JOBS_PER_PAGE = 20
MAX_PAGES = 50

# CSS 選擇器 - 基於實際網站結構的更新選擇器
SELECTORS = {
    # 主要容器選擇器
    'job_list': 'main, [data-automation="searchResults"], .jobs-list',
    
    # 職位卡片選擇器 - 基於實際調試結果
    'job_item': 'article[data-automation="normalJob"], article[data-testid="job-card"], article',
    
    # 職位標題選擇器 - 多重備選
    'title': 'h3 a, [data-automation="jobTitle"] a, [data-automation="jobTitle"], .job-title a, a[title]',
    
    # 公司名稱選擇器 - 更廣泛的選擇器
    'company': '[data-automation="jobCompany"] a, [data-automation="jobCompany"], .company-name, [data-testid="job-company"], span[title]',
    
    # 地點選擇器
    'location': '[data-automation="jobLocation"], .job-location, [data-testid="job-location"], span:contains("VIC"), span:contains("NSW"), span:contains("QLD")',
    
    # 薪資選擇器
    'salary': '[data-automation="jobSalary"], .salary, [data-testid="job-salary"], .job-salary, span:contains("$")',
    
    # 工作類型選擇器
    'job_type': '[data-automation="jobWorkType"], .work-type, [data-testid="job-work-type"], span:contains("Full time"), span:contains("Part time")',
    
    # 職位描述選擇器
    'description': '[data-automation="jobShortDescription"], .job-description, [data-testid="job-description"], p',
    
    # 發布日期選擇器
    'date_posted': '[data-automation="jobListingDate"], .date-posted, [data-testid="job-date"]',
    
    # 分頁導航選擇器
    'next_button': '[aria-label="Next"], [data-automation="page-next"], .next-page, button:has-text("Next")',
    'pagination': '[data-testid="pagination"], .pagination, nav[aria-label="Pagination"]',
    
    # 錯誤和狀態檢測選擇器
    'access_denied': 'text=Access Denied, text="Access Denied", .access-denied',
    'no_results': 'text="No jobs found", .no-results, [data-testid="no-results"]',
    'loading': '.loading, [data-testid="loading"], .spinner',
    
    # 職位詳情頁面選擇器
    'job_details': {
        'full_description': '[data-automation="jobAdDetails"], .job-details, .job-description-full',
        'requirements': '.requirements, .job-requirements',
        'benefits': '.benefits, .job-benefits',
        'apply_button': '[data-automation="job-detail-apply"], .apply-button, button:has-text("Apply")'
    },
    
    # 搜索和篩選相關選擇器
    'search': {
        'search_input': 'input[data-automation="searchKeywords"], #keywords',
        'location_input': 'input[data-automation="searchLocation"], #where',
        'search_button': 'button[data-automation="searchButton"], .search-button'
    }
}

# 錯誤消息
ERROR_MESSAGES = {
    "access_denied": "Access denied - possible anti-bot detection",
    "no_jobs_found": "No jobs found on this page",
    "page_load_failed": "Failed to load page",
    "extraction_failed": "Failed to extract job data",
    "network_error": "Network error occurred"
}

# 日誌配置
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = "INFO"
