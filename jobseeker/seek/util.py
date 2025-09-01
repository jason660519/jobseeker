"""Seek.com.au 工具函數

此模塊包含 Seek 爬蟲所需的輔助函數。
"""

import re
from typing import Optional, Tuple, List
from datetime import datetime

from jobseeker.model import JobType, CompensationInterval
from jobseeker.seek.constant import STATE_MAPPING, SALARY_INTERVAL_MAPPING


def parse_location(location_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析地點字符串，提取城市和州份
    
    Args:
        location_str: 原始地點字符串，如 "Sydney NSW" 或 "Melbourne, VIC"
        
    Returns:
        (城市, 州份) 元組
    """
    if not location_str:
        return None, None
    
    # 清理字符串
    location_str = location_str.strip()
    
    # 分割地點信息
    parts = re.split(r'[,\s]+', location_str)
    
    city = None
    state = None
    
    # 查找州份縮寫
    for part in parts:
        part_upper = part.upper().strip()
        if part_upper in STATE_MAPPING:
            state = part_upper
            break
    
    # 提取城市名稱（通常是第一個非州份的部分）
    for part in parts:
        part_clean = part.strip()
        if part_clean.upper() not in STATE_MAPPING and part_clean:
            city = part_clean
            break
    
    return city, state


def parse_salary(salary_str: str) -> Tuple[Optional[float], Optional[float], Optional[CompensationInterval]]:
    """
    解析薪資字符串，提取最低薪資、最高薪資和薪資間隔
    
    Args:
        salary_str: 原始薪資字符串，如 "$80,000 - $100,000 per year"
        
    Returns:
        (最低薪資, 最高薪資, 薪資間隔) 元組
    """
    if not salary_str:
        return None, None, None
    
    # 清理字符串
    salary_str = salary_str.strip().lower()
    
    # 確定薪資間隔
    interval = None
    for key, value in SALARY_INTERVAL_MAPPING.items():
        if key in salary_str:
            try:
                interval = CompensationInterval(value)
                break
            except ValueError:
                continue
    
    # 如果沒有找到間隔，默認為年薪
    if interval is None:
        interval = CompensationInterval.YEARLY
    
    # 移除貨幣符號、逗號和其他非數字字符（保留小數點）
    clean_salary = re.sub(r'[^\d.\s-]', '', salary_str)
    
    # 提取數字
    numbers = re.findall(r'\d+(?:\.\d+)?', clean_salary)
    
    min_amount = None
    max_amount = None
    
    if len(numbers) >= 2:
        try:
            min_amount = float(numbers[0])
            max_amount = float(numbers[1])
            # 確保最小值小於最大值
            if min_amount > max_amount:
                min_amount, max_amount = max_amount, min_amount
        except ValueError:
            pass
    elif len(numbers) == 1:
        try:
            amount = float(numbers[0])
            min_amount = amount
            max_amount = amount
        except ValueError:
            pass
    
    return min_amount, max_amount, interval


def get_job_type(job_type_str: str) -> Optional[List[JobType]]:
    """
    將工作類型字符串轉換為 JobType 枚舉
    
    Args:
        job_type_str: 工作類型字符串
        
    Returns:
        JobType 列表或 None
    """
    if not job_type_str:
        return None
    
    job_type_str = job_type_str.lower().strip()
    
    # 工作類型映射
    type_mapping = {
        'full time': JobType.FULL_TIME,
        'full-time': JobType.FULL_TIME,
        'fulltime': JobType.FULL_TIME,
        'part time': JobType.PART_TIME,
        'part-time': JobType.PART_TIME,
        'parttime': JobType.PART_TIME,
        'contract': JobType.CONTRACT,
        'contractor': JobType.CONTRACT,
        'casual': JobType.TEMPORARY,
        'temporary': JobType.TEMPORARY,
        'temp': JobType.TEMPORARY,
        'internship': JobType.INTERNSHIP,
        'intern': JobType.INTERNSHIP,
        'graduate': JobType.INTERNSHIP
    }
    
    for key, job_type in type_mapping.items():
        if key in job_type_str:
            return [job_type]
    
    return None


def is_remote_job(job_description: str, location: str = "") -> bool:
    """
    判斷是否為遠程工作
    
    Args:
        job_description: 職位描述
        location: 工作地點
        
    Returns:
        是否為遠程工作
    """
    if not job_description:
        job_description = ""
    
    text = f"{job_description} {location}".lower()
    
    remote_keywords = [
        'remote', 'work from home', 'wfh', 'telecommute', 
        'home based', 'virtual', 'distributed', 'anywhere'
    ]
    
    return any(keyword in text for keyword in remote_keywords)


def clean_text(text: str) -> str:
    """
    清理文本，移除多餘的空白字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理後的文本
    """
    if not text:
        return ""
    
    # 移除多餘的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def extract_company_url(company_element_html: str) -> Optional[str]:
    """
    從公司元素 HTML 中提取公司 URL
    
    Args:
        company_element_html: 公司元素的 HTML
        
    Returns:
        公司 URL 或 None
    """
    if not company_element_html:
        return None
    
    # 使用正則表達式提取 href 屬性
    href_match = re.search(r'href=["\']([^"\'>]+)["\']', company_element_html)
    
    if href_match:
        url = href_match.group(1)
        if url.startswith('/'):
            return f"https://www.seek.com.au{url}"
        elif url.startswith('http'):
            return url
    
    return None


def format_date(date_str: str) -> Optional[str]:
    """
    格式化日期字符串
    
    Args:
        date_str: 原始日期字符串
        
    Returns:
        格式化後的日期字符串 (YYYY-MM-DD) 或 None
    """
    if not date_str:
        return None
    
    try:
        # 嘗試解析常見的日期格式
        date_patterns = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        for pattern in date_patterns:
            try:
                parsed_date = datetime.strptime(date_str.strip(), pattern)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # 如果無法解析，返回當前日期
        return datetime.now().strftime('%Y-%m-%d')
        
    except Exception:
        return None


def validate_url(url: str) -> bool:
    """
    驗證 URL 是否有效
    
    Args:
        url: 要驗證的 URL
        
    Returns:
        URL 是否有效
    """
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # 域名
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # 頂級域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP 地址
        r'(?::\d+)?'  # 可選端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def generate_job_id(title: str, company: str, location: str) -> str:
    """
    生成唯一的職位 ID
    
    Args:
        title: 職位標題
        company: 公司名稱
        location: 工作地點
        
    Returns:
        唯一的職位 ID
    """
    import hashlib
    
    # 組合字符串
    combined = f"{title}_{company}_{location}".lower()
    
    # 生成 MD5 哈希
    hash_object = hashlib.md5(combined.encode())
    hash_hex = hash_object.hexdigest()
    
    return f"seek_{hash_hex[:12]}"


def extract_skills_from_description(description: str) -> List[str]:
    """
    從職位描述中提取技能關鍵詞
    
    Args:
        description: 職位描述
        
    Returns:
        技能關鍵詞列表
    """
    if not description:
        return []
    
    # 常見技能關鍵詞
    skill_keywords = [
        # 程式語言
        'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'swift', 'kotlin', 'typescript', 'scala', 'r', 'matlab', 'sql',
        
        # 框架和庫
        'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
        'laravel', 'rails', 'asp.net', 'jquery', 'bootstrap',
        
        # 數據庫
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle',
        'sqlite', 'cassandra', 'dynamodb',
        
        # 雲平台
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
        
        # 其他技術
        'git', 'linux', 'agile', 'scrum', 'devops', 'ci/cd', 'api', 'rest',
        'graphql', 'microservices', 'machine learning', 'ai', 'data science'
    ]
    
    description_lower = description.lower()
    found_skills = []
    
    for skill in skill_keywords:
        if skill in description_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))  # 去重
