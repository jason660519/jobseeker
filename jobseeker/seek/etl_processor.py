# -*- coding: utf-8 -*-
"""
Seek ETL數據處理模組
負責將爬蟲引擎抓取的原始數據進行清洗、轉換和標準化處理
輸出符合JobPost模型的結構化數據

Author: JobSpy Team
Date: 2024
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from ..model import JobPost, JobType, Country, Currency
from ..util import extract_emails_from_text, extract_salary_from_text


class SeekETLProcessor:
    """
    Seek數據ETL處理器
    負責數據清洗、轉換、標準化和質量控制
    """
    
    def __init__(self, 
                 output_path: str = None,
                 enable_data_validation: bool = True,
                 enable_deduplication: bool = True):
        """
        初始化ETL處理器
        
        Args:
            output_path: 輸出數據路徑
            enable_data_validation: 是否啟用數據驗證
            enable_deduplication: 是否啟用去重處理
        """
        self.output_path = Path(output_path) if output_path else Path("./seek_etl_output")
        self.output_path.mkdir(exist_ok=True)
        
        self.enable_data_validation = enable_data_validation
        self.enable_deduplication = enable_deduplication
        
        # 設置日誌
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 數據質量統計
        self.quality_stats = {
            'total_processed': 0,
            'valid_jobs': 0,
            'invalid_jobs': 0,
            'duplicates_removed': 0,
            'salary_extracted': 0,
            'emails_extracted': 0,
            'data_enriched': 0
        }
        
        # 去重緩存
        self.processed_urls = set()
        self.processed_titles_companies = set()
        
        # 薪資解析正則表達式
        self.salary_patterns = {
            'annual': re.compile(r'\$([\d,]+)(?:\s*-\s*\$?([\d,]+))?\s*(?:per\s+)?(?:year|annually|pa|p\.a\.)', re.IGNORECASE),
            'hourly': re.compile(r'\$([\d,]+(?:\.\d{2})?)(?:\s*-\s*\$?([\d,]+(?:\.\d{2})?))?\s*(?:per\s+)?(?:hour|hourly|ph|p\.h\.)', re.IGNORECASE),
            'daily': re.compile(r'\$([\d,]+)(?:\s*-\s*\$?([\d,]+))?\s*(?:per\s+)?(?:day|daily|pd|p\.d\.)', re.IGNORECASE),
            'range': re.compile(r'\$([\d,]+)\s*(?:-|to)\s*\$?([\d,]+)', re.IGNORECASE)
        }
        
        # 工作類型映射
        self.job_type_mapping = {
            'full time': JobType.FULL_TIME,
            'full-time': JobType.FULL_TIME,
            'fulltime': JobType.FULL_TIME,
            'part time': JobType.PART_TIME,
            'part-time': JobType.PART_TIME,
            'parttime': JobType.PART_TIME,
            'contract': JobType.CONTRACT,
            'contractor': JobType.CONTRACT,
            'temporary': JobType.TEMPORARY,
            'temp': JobType.TEMPORARY,
            'internship': JobType.INTERNSHIP,
            'intern': JobType.INTERNSHIP,
            'casual': JobType.PART_TIME,
            'freelance': JobType.CONTRACT
        }
    
    def process_raw_data(self, raw_data: Union[Dict, List[Dict], str]) -> List[JobPost]:
        """
        處理原始數據，轉換為JobPost對象列表
        
        Args:
            raw_data: 原始數據（字典、列表或JSON字符串）
            
        Returns:
            List[JobPost]: 處理後的JobPost對象列表
        """
        try:
            # 數據格式標準化
            normalized_data = self._normalize_input_data(raw_data)
            
            processed_jobs = []
            
            for job_data in normalized_data:
                # 數據清洗和轉換
                cleaned_job = self._clean_job_data(job_data)
                
                if cleaned_job:
                    # 轉換為JobPost對象
                    job_post = self._convert_to_job_post(cleaned_job)
                    
                    if job_post:
                        # 數據驗證
                        if self._validate_job_post(job_post):
                            # 去重檢查
                            if not self._is_duplicate(job_post):
                                processed_jobs.append(job_post)
                                self.quality_stats['valid_jobs'] += 1
                            else:
                                self.quality_stats['duplicates_removed'] += 1
                        else:
                            self.quality_stats['invalid_jobs'] += 1
                
                self.quality_stats['total_processed'] += 1
            
            self.logger.info(f"ETL處理完成: {len(processed_jobs)} 個有效職位")
            return processed_jobs
            
        except Exception as e:
            self.logger.error(f"ETL處理失敗: {e}")
            return []
    
    def _normalize_input_data(self, raw_data: Union[Dict, List[Dict], str]) -> List[Dict]:
        """
        標準化輸入數據格式
        
        Args:
            raw_data: 原始輸入數據
            
        Returns:
            List[Dict]: 標準化後的數據列表
        """
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                self.logger.error("無效的JSON字符串")
                return []
        
        if isinstance(raw_data, dict):
            # 檢查是否包含jobs列表
            if 'jobs' in raw_data:
                return raw_data['jobs']
            else:
                return [raw_data]
        
        if isinstance(raw_data, list):
            return raw_data
        
        return []
    
    def _clean_job_data(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        清洗單個職位數據
        
        Args:
            job_data: 原始職位數據
            
        Returns:
            Optional[Dict[str, Any]]: 清洗後的職位數據
        """
        try:
            cleaned = {}
            
            # 清洗標題
            title = job_data.get('title', '').strip()
            if not title or title.lower() in ['未知職位', 'unknown', 'n/a']:
                return None
            cleaned['title'] = self._clean_text(title)
            
            # 清洗公司名稱
            company = job_data.get('company', '').strip()
            if not company or company.lower() in ['未知公司', 'unknown', 'n/a']:
                return None
            cleaned['company'] = self._clean_text(company)
            
            # 清洗地點
            location = job_data.get('location', '').strip()
            cleaned['location'] = self._clean_text(location) if location else 'Australia'
            
            # 清洗描述
            description = job_data.get('description', '').strip()
            cleaned['description'] = self._clean_text(description)
            
            # 清洗URL
            url = job_data.get('url', '').strip()
            cleaned['url'] = url if self._is_valid_url(url) else ''
            
            # 處理薪資信息
            salary_text = job_data.get('salary', '').strip()
            cleaned['salary_info'] = self._extract_salary_info(salary_text)
            
            # 提取郵箱
            all_text = f"{title} {company} {description} {salary_text}"
            emails = extract_emails_from_text(all_text)
            cleaned['emails'] = list(set(emails)) if emails else []
            
            if emails:
                self.quality_stats['emails_extracted'] += 1
            
            # 添加元數據
            cleaned['source'] = job_data.get('source', 'seek.com.au')
            cleaned['extracted_at'] = job_data.get('extracted_at', datetime.now().isoformat())
            cleaned['job_type'] = self._extract_job_type(f"{title} {description}")
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"數據清洗失敗: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本內容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清洗後的文本
        """
        if not text:
            return ''
        
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除HTML標籤
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除特殊字符（保留基本標點）
        text = re.sub(r'[^\w\s\-.,!?()$%&@#]', '', text)
        
        return text.strip()
    
    def _is_valid_url(self, url: str) -> bool:
        """
        驗證URL格式
        
        Args:
            url: URL字符串
            
        Returns:
            bool: 是否為有效URL
        """
        if not url:
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def _extract_salary_info(self, salary_text: str) -> Dict[str, Any]:
        """
        提取薪資信息
        
        Args:
            salary_text: 薪資文本
            
        Returns:
            Dict[str, Any]: 薪資信息字典
        """
        salary_info = {
            'raw_text': salary_text,
            'min_amount': None,
            'max_amount': None,
            'currency': 'AUD',
            'interval': None,
            'is_estimated': False
        }
        
        if not salary_text:
            return salary_info
        
        try:
            # 嘗試各種薪資模式
            for interval, pattern in self.salary_patterns.items():
                match = pattern.search(salary_text)
                if match:
                    salary_info['interval'] = interval
                    
                    # 提取金額
                    min_amount = match.group(1).replace(',', '')
                    max_amount = match.group(2) if match.group(2) else None
                    
                    salary_info['min_amount'] = float(min_amount)
                    if max_amount:
                        salary_info['max_amount'] = float(max_amount.replace(',', ''))
                    
                    self.quality_stats['salary_extracted'] += 1
                    break
            
            # 檢查是否為估算薪資
            if any(word in salary_text.lower() for word in ['estimated', 'approx', 'circa', '約', '估計']):
                salary_info['is_estimated'] = True
            
        except Exception as e:
            self.logger.error(f"薪資信息提取失敗: {e}")
        
        return salary_info
    
    def _extract_job_type(self, text: str) -> JobType:
        """
        從文本中提取工作類型
        
        Args:
            text: 包含工作類型信息的文本
            
        Returns:
            JobType: 工作類型枚舉
        """
        text_lower = text.lower()
        
        for keyword, job_type in self.job_type_mapping.items():
            if keyword in text_lower:
                return job_type
        
        # 默認返回全職
        return JobType.FULL_TIME
    
    def _convert_to_job_post(self, cleaned_data: Dict[str, Any]) -> Optional[JobPost]:
        """
        將清洗後的數據轉換為JobPost對象
        
        Args:
            cleaned_data: 清洗後的職位數據
            
        Returns:
            Optional[JobPost]: JobPost對象
        """
        try:
            salary_info = cleaned_data.get('salary_info', {})
            
            job_post = JobPost(
                title=cleaned_data['title'],
                company=cleaned_data['company'],
                location=cleaned_data['location'],
                job_type=cleaned_data.get('job_type', JobType.FULL_TIME),
                salary_min=salary_info.get('min_amount'),
                salary_max=salary_info.get('max_amount'),
                currency=Currency.AUD,
                interval=salary_info.get('interval'),
                description=cleaned_data.get('description', ''),
                job_url=cleaned_data.get('url', ''),
                job_url_direct=cleaned_data.get('url', ''),
                source='seek',
                country=Country.AUSTRALIA,
                date_posted=self._parse_date(cleaned_data.get('extracted_at')),
                emails=cleaned_data.get('emails', []),
                is_remote=self._detect_remote_work(cleaned_data.get('description', '') + ' ' + cleaned_data.get('location', '')),
                compensation=self._build_compensation_object(salary_info)
            )
            
            return job_post
            
        except Exception as e:
            self.logger.error(f"JobPost對象創建失敗: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串
            
        Returns:
            Optional[datetime]: 解析後的日期對象
        """
        if not date_str:
            return datetime.now()
        
        try:
            # 嘗試ISO格式
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # 嘗試其他常見格式
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except:
                return datetime.now()
    
    def _detect_remote_work(self, text: str) -> bool:
        """
        檢測是否為遠程工作
        
        Args:
            text: 包含工作信息的文本
            
        Returns:
            bool: 是否為遠程工作
        """
        remote_keywords = [
            'remote', 'work from home', 'wfh', 'telecommute',
            'virtual', 'distributed', 'anywhere', 'home-based',
            '遠程', '在家工作', '居家辦公'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in remote_keywords)
    
    def _build_compensation_object(self, salary_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        構建薪酬對象
        
        Args:
            salary_info: 薪資信息字典
            
        Returns:
            Optional[Dict[str, Any]]: 薪酬對象
        """
        if not salary_info.get('min_amount'):
            return None
        
        return {
            'min_amount': salary_info.get('min_amount'),
            'max_amount': salary_info.get('max_amount'),
            'currency': salary_info.get('currency', 'AUD'),
            'interval': salary_info.get('interval'),
            'is_estimated': salary_info.get('is_estimated', False)
        }
    
    def _validate_job_post(self, job_post: JobPost) -> bool:
        """
        驗證JobPost對象的數據質量
        
        Args:
            job_post: JobPost對象
            
        Returns:
            bool: 是否通過驗證
        """
        if not self.enable_data_validation:
            return True
        
        try:
            # 必填字段檢查
            if not job_post.title or len(job_post.title.strip()) < 2:
                return False
            
            if not job_post.company or len(job_post.company.strip()) < 2:
                return False
            
            # 薪資邏輯檢查
            if job_post.salary_min and job_post.salary_max:
                if job_post.salary_min > job_post.salary_max:
                    return False
                
                # 薪資合理性檢查（澳洲最低工資約$20/小時）
                if job_post.interval == 'hourly' and job_post.salary_min < 15:
                    return False
                elif job_post.interval == 'annual' and job_post.salary_min < 30000:
                    return False
            
            # URL格式檢查
            if job_post.job_url and not self._is_valid_url(job_post.job_url):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"數據驗證失敗: {e}")
            return False
    
    def _is_duplicate(self, job_post: JobPost) -> bool:
        """
        檢查是否為重複職位
        
        Args:
            job_post: JobPost對象
            
        Returns:
            bool: 是否為重複
        """
        if not self.enable_deduplication:
            return False
        
        # URL去重
        if job_post.job_url and job_post.job_url in self.processed_urls:
            return True
        
        # 標題+公司去重
        title_company_key = f"{job_post.title.lower()}_{job_post.company.lower()}"
        if title_company_key in self.processed_titles_companies:
            return True
        
        # 記錄已處理的職位
        if job_post.job_url:
            self.processed_urls.add(job_post.job_url)
        self.processed_titles_companies.add(title_company_key)
        
        return False
    
    def export_to_json(self, job_posts: List[JobPost], filename: str = None) -> str:
        """
        導出JobPost列表為JSON格式
        
        Args:
            job_posts: JobPost對象列表
            filename: 輸出文件名
            
        Returns:
            str: 輸出文件路徑
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"seek_jobs_{timestamp}.json"
            
            output_file = self.output_path / filename
            
            # 轉換為字典格式
            jobs_data = []
            for job in job_posts:
                job_dict = asdict(job)
                # 處理日期序列化
                if job_dict.get('date_posted'):
                    job_dict['date_posted'] = job_dict['date_posted'].isoformat()
                jobs_data.append(job_dict)
            
            # 構建輸出數據
            output_data = {
                'metadata': {
                    'total_jobs': len(job_posts),
                    'exported_at': datetime.now().isoformat(),
                    'source': 'seek.com.au',
                    'quality_stats': self.quality_stats
                },
                'jobs': jobs_data
            }
            
            # 寫入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"數據已導出到: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"數據導出失敗: {e}")
            return ""
    
    def get_quality_report(self) -> Dict[str, Any]:
        """
        獲取數據質量報告
        
        Returns:
            Dict[str, Any]: 質量報告
        """
        total = self.quality_stats['total_processed']
        if total == 0:
            return self.quality_stats
        
        return {
            **self.quality_stats,
            'success_rate': round(self.quality_stats['valid_jobs'] / total * 100, 2),
            'duplicate_rate': round(self.quality_stats['duplicates_removed'] / total * 100, 2),
            'salary_extraction_rate': round(self.quality_stats['salary_extracted'] / total * 100, 2),
            'email_extraction_rate': round(self.quality_stats['emails_extracted'] / total * 100, 2)
        }


# 使用示例
if __name__ == "__main__":
    # 創建ETL處理器
    etl_processor = SeekETLProcessor(
        output_path="./seek_etl_output",
        enable_data_validation=True,
        enable_deduplication=True
    )
    
    # 示例原始數據
    sample_raw_data = [
        {
            'title': 'Senior Python Developer',
            'company': 'Tech Solutions Pty Ltd',
            'location': 'Sydney, NSW',
            'salary': '$90,000 - $120,000 per year',
            'description': 'We are looking for an experienced Python developer to join our team. Remote work available.',
            'url': 'https://www.seek.com.au/job/12345',
            'extracted_at': '2024-01-15T10:30:00'
        },
        {
            'title': 'Data Scientist',
            'company': 'Analytics Corp',
            'location': 'Melbourne, VIC',
            'salary': '$45 - $65 per hour',
            'description': 'Contract position for data analysis and machine learning projects.',
            'url': 'https://www.seek.com.au/job/67890',
            'extracted_at': '2024-01-15T11:00:00'
        }
    ]
    
    # 處理數據
    processed_jobs = etl_processor.process_raw_data(sample_raw_data)
    
    # 導出結果
    if processed_jobs:
        output_file = etl_processor.export_to_json(processed_jobs)
        print(f"處理完成，輸出文件: {output_file}")
        print(f"質量報告: {etl_processor.get_quality_report()}")
    else:
        print("沒有有效的職位數據")