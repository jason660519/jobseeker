#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 測試固定資料

這個檔案包含了 JobSpy 測試所需的固定資料和模擬資料，
用於提供一致的測試環境和可重複的測試結果。

作者: JobSpy Team
日期: 2024
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


# ==================== 基本測試資料 ====================

SAMPLE_JOB_DATA = {
    "title": "Senior Python Developer",
    "company": "Tech Solutions Inc",
    "location": "Sydney, NSW",
    "description": "We are looking for an experienced Python developer to join our team. The ideal candidate will have strong experience with Django, Flask, and modern Python frameworks.",
    "salary_min": 80000,
    "salary_max": 120000,
    "currency": "AUD",
    "job_type": "fulltime",
    "date_posted": "2024-01-15",
    "job_url": "https://example.com/jobs/python-developer-123",
    "site": "indeed",
    "remote": False,
    "benefits": ["Health Insurance", "Flexible Hours", "Remote Work Options"],
    "requirements": ["Python", "Django", "PostgreSQL", "Git", "AWS"]
}

SAMPLE_JOBS_LIST = [
    {
        "title": "Python Developer",
        "company": "StartupCorp",
        "location": "Melbourne, VIC",
        "description": "Join our innovative startup as a Python developer.",
        "salary_min": 70000,
        "salary_max": 90000,
        "currency": "AUD",
        "job_type": "fulltime",
        "date_posted": "2024-01-10",
        "job_url": "https://example.com/jobs/python-dev-456",
        "site": "linkedin",
        "remote": True
    },
    {
        "title": "Data Scientist",
        "company": "Analytics Pro",
        "location": "Brisbane, QLD",
        "description": "Seeking a data scientist with machine learning expertise.",
        "salary_min": 90000,
        "salary_max": 130000,
        "currency": "AUD",
        "job_type": "fulltime",
        "date_posted": "2024-01-12",
        "job_url": "https://example.com/jobs/data-scientist-789",
        "site": "glassdoor",
        "remote": False
    },
    {
        "title": "Frontend Developer",
        "company": "WebDesign Co",
        "location": "Perth, WA",
        "description": "Looking for a React.js frontend developer.",
        "salary_min": 65000,
        "salary_max": 85000,
        "currency": "AUD",
        "job_type": "contract",
        "date_posted": "2024-01-08",
        "job_url": "https://example.com/jobs/frontend-dev-101",
        "site": "seek",
        "remote": True
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudTech Solutions",
        "location": "Adelaide, SA",
        "description": "DevOps engineer with AWS and Kubernetes experience.",
        "salary_min": 95000,
        "salary_max": 140000,
        "currency": "AUD",
        "job_type": "fulltime",
        "date_posted": "2024-01-14",
        "job_url": "https://example.com/jobs/devops-eng-202",
        "site": "indeed",
        "remote": False
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Innovations",
        "location": "Sydney, NSW",
        "description": "ML engineer to develop and deploy machine learning models.",
        "salary_min": 100000,
        "salary_max": 150000,
        "currency": "AUD",
        "job_type": "fulltime",
        "date_posted": "2024-01-16",
        "job_url": "https://example.com/jobs/ml-engineer-303",
        "site": "linkedin",
        "remote": True
    }
]


# ==================== 搜尋參數測試資料 ====================

VALID_SEARCH_PARAMS = [
    {
        "site_name": "indeed",
        "search_term": "python developer",
        "location": "Sydney",
        "results_wanted": 10,
        "distance": 25,
        "job_type": "fulltime",
        "remote": False
    },
    {
        "site_name": "linkedin",
        "search_term": "data scientist",
        "location": "Melbourne",
        "results_wanted": 15,
        "distance": 50,
        "job_type": "contract",
        "remote": True
    },
    {
        "site_name": ["indeed", "linkedin"],
        "search_term": "software engineer",
        "location": "Brisbane",
        "results_wanted": 20,
        "distance": 10,
        "job_type": "parttime",
        "remote": None
    }
]

INVALID_SEARCH_PARAMS = [
    {
        "site_name": "invalid_site",
        "search_term": "test",
        "location": "Sydney",
        "results_wanted": 5
    },
    {
        "site_name": "indeed",
        "search_term": "",
        "location": "Melbourne",
        "results_wanted": 5
    },
    {
        "site_name": "linkedin",
        "search_term": "test",
        "location": "Brisbane",
        "results_wanted": -1
    },
    {
        "site_name": "glassdoor",
        "search_term": "test",
        "location": "",
        "results_wanted": 5
    }
]


# ==================== 網站特定測試資料 ====================

SITE_SPECIFIC_DATA = {
    "indeed": {
        "base_url": "https://au.indeed.com",
        "search_url": "https://au.indeed.com/jobs",
        "valid_locations": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
        "job_types": ["fulltime", "parttime", "contract", "temporary"],
        "max_results": 1000,
        "rate_limit": 1.0  # 秒
    },
    "linkedin": {
        "base_url": "https://www.linkedin.com",
        "search_url": "https://www.linkedin.com/jobs/search",
        "valid_locations": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
        "job_types": ["fulltime", "parttime", "contract", "internship"],
        "max_results": 1000,
        "rate_limit": 2.0
    },
    "glassdoor": {
        "base_url": "https://www.glassdoor.com.au",
        "search_url": "https://www.glassdoor.com.au/Job/jobs.htm",
        "valid_locations": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
        "job_types": ["fulltime", "parttime", "contract"],
        "max_results": 500,
        "rate_limit": 1.5
    },
    "seek": {
        "base_url": "https://www.seek.com.au",
        "search_url": "https://www.seek.com.au/jobs",
        "valid_locations": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
        "job_types": ["fulltime", "parttime", "contract", "casual"],
        "max_results": 1000,
        "rate_limit": 1.0
    }
}


# ==================== Mock 響應資料 ====================

MOCK_HTML_RESPONSE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Search Results</title>
</head>
<body>
    <div class="job-card">
        <h3 class="job-title">Python Developer</h3>
        <div class="company-name">Tech Company</div>
        <div class="job-location">Sydney, NSW</div>
        <div class="job-description">Looking for a Python developer...</div>
        <div class="salary">$80,000 - $100,000</div>
    </div>
    <div class="job-card">
        <h3 class="job-title">Data Scientist</h3>
        <div class="company-name">Analytics Corp</div>
        <div class="job-location">Melbourne, VIC</div>
        <div class="job-description">Seeking a data scientist...</div>
        <div class="salary">$90,000 - $120,000</div>
    </div>
</body>
</html>
"""

MOCK_JSON_RESPONSE = {
    "jobs": [
        {
            "id": "job_001",
            "title": "Python Developer",
            "company": "Tech Solutions",
            "location": "Sydney, NSW",
            "description": "Python developer position...",
            "salary": {
                "min": 80000,
                "max": 100000,
                "currency": "AUD"
            },
            "type": "fulltime",
            "posted_date": "2024-01-15",
            "url": "https://example.com/job/001"
        },
        {
            "id": "job_002",
            "title": "Data Scientist",
            "company": "Analytics Pro",
            "location": "Melbourne, VIC",
            "description": "Data scientist role...",
            "salary": {
                "min": 90000,
                "max": 120000,
                "currency": "AUD"
            },
            "type": "fulltime",
            "posted_date": "2024-01-12",
            "url": "https://example.com/job/002"
        }
    ],
    "total_results": 2,
    "page": 1,
    "per_page": 10
}

MOCK_ERROR_RESPONSE = {
    "error": {
        "code": 429,
        "message": "Rate limit exceeded",
        "details": "Too many requests. Please try again later."
    }
}


# ==================== 測試配置資料 ====================

TEST_CONFIGURATIONS = {
    "basic": {
        "timeout": 30,
        "retries": 3,
        "delay": 1.0,
        "user_agent": "JobSpy-Test/1.0"
    },
    "aggressive": {
        "timeout": 10,
        "retries": 1,
        "delay": 0.5,
        "user_agent": "JobSpy-Aggressive/1.0"
    },
    "conservative": {
        "timeout": 60,
        "retries": 5,
        "delay": 3.0,
        "user_agent": "JobSpy-Conservative/1.0"
    }
}

ASYNC_TEST_CONFIGURATIONS = {
    "low_concurrency": {
        "max_concurrent_requests": 2,
        "request_delay": 2.0,
        "timeout": 30.0,
        "mode": "asyncio"
    },
    "medium_concurrency": {
        "max_concurrent_requests": 5,
        "request_delay": 1.0,
        "timeout": 30.0,
        "mode": "asyncio"
    },
    "high_concurrency": {
        "max_concurrent_requests": 10,
        "request_delay": 0.5,
        "timeout": 30.0,
        "mode": "threaded"
    }
}


# ==================== 效能測試資料 ====================

PERFORMANCE_BENCHMARKS = {
    "small_request": {
        "results_wanted": 5,
        "expected_time": 15,  # 秒
        "max_memory": 50  # MB
    },
    "medium_request": {
        "results_wanted": 20,
        "expected_time": 30,
        "max_memory": 100
    },
    "large_request": {
        "results_wanted": 50,
        "expected_time": 60,
        "max_memory": 200
    },
    "stress_test": {
        "duration": 300,  # 5 分鐘
        "requests_per_minute": 10,
        "max_memory": 500,
        "min_success_rate": 80  # %
    }
}


# ==================== 快取測試資料 ====================

CACHE_TEST_DATA = {
    "cache_keys": [
        "indeed_python_sydney_10",
        "linkedin_data_scientist_melbourne_15",
        "glassdoor_software_engineer_brisbane_20"
    ],
    "cache_values": [
        {"jobs": SAMPLE_JOBS_LIST[:2], "timestamp": "2024-01-15T10:00:00Z"},
        {"jobs": SAMPLE_JOBS_LIST[2:4], "timestamp": "2024-01-15T11:00:00Z"},
        {"jobs": SAMPLE_JOBS_LIST[4:], "timestamp": "2024-01-15T12:00:00Z"}
    ],
    "expired_data": {
        "jobs": SAMPLE_JOBS_LIST[:1],
        "timestamp": "2024-01-01T00:00:00Z"  # 過期資料
    }
}


# ==================== 錯誤測試資料 ====================

ERROR_TEST_SCENARIOS = [
    {
        "name": "network_timeout",
        "exception": "requests.exceptions.Timeout",
        "message": "Request timed out",
        "expected_behavior": "retry_or_fail"
    },
    {
        "name": "connection_error",
        "exception": "requests.exceptions.ConnectionError",
        "message": "Failed to establish connection",
        "expected_behavior": "retry_or_fail"
    },
    {
        "name": "http_404",
        "exception": "requests.exceptions.HTTPError",
        "message": "404 Not Found",
        "expected_behavior": "fail_immediately"
    },
    {
        "name": "http_429",
        "exception": "requests.exceptions.HTTPError",
        "message": "429 Too Many Requests",
        "expected_behavior": "retry_with_backoff"
    },
    {
        "name": "parsing_error",
        "exception": "ValueError",
        "message": "Failed to parse response",
        "expected_behavior": "log_and_continue"
    }
]


# ==================== 資料品質測試資料 ====================

DATA_QUALITY_TEST_CASES = {
    "duplicate_jobs": [
        # 完全重複
        {
            "title": "Python Developer",
            "company": "Tech Corp",
            "location": "Sydney",
            "job_url": "https://example.com/job/123"
        },
        {
            "title": "Python Developer",
            "company": "Tech Corp",
            "location": "Sydney",
            "job_url": "https://example.com/job/123"
        },
        # 近似重複
        {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "location": "Sydney, NSW",
            "job_url": "https://example.com/job/124"
        }
    ],
    "incomplete_jobs": [
        {
            "title": "Python Developer",
            "company": "",  # 缺少公司名稱
            "location": "Sydney"
        },
        {
            "title": "",  # 缺少職位標題
            "company": "Tech Corp",
            "location": "Melbourne"
        },
        {
            "title": "Data Scientist",
            "company": "Analytics Pro",
            "location": ""  # 缺少地點
        }
    ],
    "malformed_data": [
        {
            "title": "Python Developer\n\n\t",  # 包含空白字符
            "company": "  Tech Corp  ",  # 前後空格
            "location": "Sydney, NSW, Australia",
            "salary_min": "80000",  # 字串而非數字
            "salary_max": "not_a_number",  # 無效數字
            "date_posted": "invalid_date"  # 無效日期
        }
    ]
}


# ==================== 輔助函數 ====================

def create_sample_dataframe(num_jobs: int = 5) -> pd.DataFrame:
    """創建範例職位 DataFrame"""
    jobs = SAMPLE_JOBS_LIST[:num_jobs] if num_jobs <= len(SAMPLE_JOBS_LIST) else SAMPLE_JOBS_LIST
    return pd.DataFrame(jobs)


def create_test_search_params(site: str = "indeed", term: str = "python") -> Dict[str, Any]:
    """創建測試搜尋參數"""
    return {
        "site_name": site,
        "search_term": term,
        "location": "Sydney",
        "results_wanted": 10,
        "distance": 25,
        "job_type": "fulltime"
    }


def create_mock_response_data(num_jobs: int = 3) -> Dict[str, Any]:
    """創建 Mock 響應資料"""
    jobs = SAMPLE_JOBS_LIST[:num_jobs]
    return {
        "jobs": jobs,
        "total_results": num_jobs,
        "page": 1,
        "per_page": 10,
        "timestamp": datetime.now().isoformat()
    }


def create_performance_test_data(size: str = "medium") -> Dict[str, Any]:
    """創建效能測試資料"""
    if size in PERFORMANCE_BENCHMARKS:
        return PERFORMANCE_BENCHMARKS[size].copy()
    else:
        return PERFORMANCE_BENCHMARKS["medium"].copy()


def create_async_test_config(level: str = "medium_concurrency") -> Dict[str, Any]:
    """創建非同步測試配置"""
    if level in ASYNC_TEST_CONFIGURATIONS:
        return ASYNC_TEST_CONFIGURATIONS[level].copy()
    else:
        return ASYNC_TEST_CONFIGURATIONS["medium_concurrency"].copy()


def get_site_test_data(site_name: str) -> Dict[str, Any]:
    """獲取特定網站的測試資料"""
    return SITE_SPECIFIC_DATA.get(site_name, {})


def create_cache_test_scenario(scenario: str = "basic") -> Dict[str, Any]:
    """創建快取測試場景"""
    scenarios = {
        "basic": {
            "cache_size": 100,
            "ttl": 3600,  # 1 小時
            "test_keys": CACHE_TEST_DATA["cache_keys"][:2]
        },
        "large": {
            "cache_size": 1000,
            "ttl": 7200,  # 2 小時
            "test_keys": CACHE_TEST_DATA["cache_keys"]
        },
        "expiry": {
            "cache_size": 50,
            "ttl": 1,  # 1 秒（快速過期）
            "test_keys": CACHE_TEST_DATA["cache_keys"][:1]
        }
    }
    
    return scenarios.get(scenario, scenarios["basic"])


def create_error_test_scenario(error_type: str) -> Dict[str, Any]:
    """創建錯誤測試場景"""
    for scenario in ERROR_TEST_SCENARIOS:
        if scenario["name"] == error_type:
            return scenario.copy()
    
    # 預設錯誤場景
    return ERROR_TEST_SCENARIOS[0].copy()


def validate_job_data(job_data: Dict[str, Any]) -> List[str]:
    """驗證職位資料並返回錯誤列表"""
    errors = []
    
    # 必要欄位檢查
    required_fields = ["title", "company", "location"]
    for field in required_fields:
        if not job_data.get(field):
            errors.append(f"缺少必要欄位: {field}")
        elif isinstance(job_data[field], str) and not job_data[field].strip():
            errors.append(f"欄位為空: {field}")
    
    # 資料類型檢查
    if "salary_min" in job_data and job_data["salary_min"] is not None:
        try:
            float(job_data["salary_min"])
        except (ValueError, TypeError):
            errors.append("salary_min 必須是數字")
    
    if "salary_max" in job_data and job_data["salary_max"] is not None:
        try:
            float(job_data["salary_max"])
        except (ValueError, TypeError):
            errors.append("salary_max 必須是數字")
    
    # 日期格式檢查
    if "date_posted" in job_data and job_data["date_posted"]:
        try:
            datetime.fromisoformat(job_data["date_posted"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("date_posted 日期格式無效")
    
    return errors


def clean_test_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """清理測試資料"""
    cleaned = job_data.copy()
    
    # 清理字串欄位
    string_fields = ["title", "company", "location", "description"]
    for field in string_fields:
        if field in cleaned and isinstance(cleaned[field], str):
            cleaned[field] = cleaned[field].strip()
    
    # 轉換數字欄位
    numeric_fields = ["salary_min", "salary_max"]
    for field in numeric_fields:
        if field in cleaned and cleaned[field] is not None:
            try:
                cleaned[field] = float(cleaned[field])
            except (ValueError, TypeError):
                cleaned[field] = None
    
    return cleaned


# ==================== 導出所有測試資料 ====================

__all__ = [
    # 基本資料
    "SAMPLE_JOB_DATA",
    "SAMPLE_JOBS_LIST",
    
    # 搜尋參數
    "VALID_SEARCH_PARAMS",
    "INVALID_SEARCH_PARAMS",
    
    # 網站資料
    "SITE_SPECIFIC_DATA",
    
    # Mock 資料
    "MOCK_HTML_RESPONSE",
    "MOCK_JSON_RESPONSE",
    "MOCK_ERROR_RESPONSE",
    
    # 配置資料
    "TEST_CONFIGURATIONS",
    "ASYNC_TEST_CONFIGURATIONS",
    
    # 效能資料
    "PERFORMANCE_BENCHMARKS",
    
    # 快取資料
    "CACHE_TEST_DATA",
    
    # 錯誤資料
    "ERROR_TEST_SCENARIOS",
    
    # 資料品質
    "DATA_QUALITY_TEST_CASES",
    
    # 輔助函數
    "create_sample_dataframe",
    "create_test_search_params",
    "create_mock_response_data",
    "create_performance_test_data",
    "create_async_test_config",
    "get_site_test_data",
    "create_cache_test_scenario",
    "create_error_test_scenario",
    "validate_job_data",
    "clean_test_data"
]