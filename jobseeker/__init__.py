from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Dict, Any, Optional, Union, List
import asyncio

import pandas as pd

from jobseeker.bayt import BaytScraper
from jobseeker.bdjobs import BDJobs
from jobseeker.glassdoor import Glassdoor
from jobseeker.google import Google
from jobseeker.indeed import Indeed
from jobseeker.linkedin import LinkedIn
from jobseeker.naukri import Naukri
from jobseeker.seek import SeekScraper
from jobseeker.model import JobType, Location, JobResponse, Country
from jobseeker.model import SalarySource, ScraperInput, Site
from jobseeker.util import (
    set_logger_level,
    extract_salary,
    create_logger,
    get_enum_from_value,
    map_str_to_site,
    convert_to_annual,
    desired_order,
)
from jobseeker.ziprecruiter import ZipRecruiter
from jobseeker.enhanced_config import EnhancedScraperConfig

# 導入非同步爬蟲功能
from jobseeker.async_scraping import (
    AsyncConfig, AsyncMode, AsyncScrapingManager,
    async_scrape_jobs as _async_scrape_jobs,
    get_global_async_manager, AsyncScrapingResult
)


# Update the SCRAPER_MAPPING dictionary in the scrape_jobs function

def scrape_jobs(
    site_name: str | list[str] | Site | list[Site] | None = None,
    search_term: str | None = None,
    google_search_term: str | None = None,
    location: str | None = None,
    distance: int | None = 50,
    is_remote: bool = False,
    job_type: str | None = None,
    easy_apply: bool | None = None,
    results_wanted: int = 15,
    country_indeed: str = "usa",
    proxies: list[str] | str | None = None,
    ca_cert: str | None = None,
    description_format: str = "markdown",
    linkedin_fetch_description: bool | None = False,
    linkedin_company_ids: list[int] | None = None,
    offset: int | None = 0,
    hours_old: int = None,
    enforce_annual_salary: bool = False,
    verbose: int = 0,
    user_agent: str = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Scrapes job data from job boards concurrently
    :return: Pandas DataFrame containing job data
    """
    # 基礎爬蟲映射
    SCRAPER_MAPPING = {
        Site.LINKEDIN: LinkedIn,
        Site.INDEED: Indeed,
        Site.ZIP_RECRUITER: ZipRecruiter,
        Site.GLASSDOOR: Glassdoor,
        Site.GOOGLE: Google,
        Site.BAYT: BaytScraper,
        Site.NAUKRI: Naukri,
        Site.BDJOBS: BDJobs,
        Site.SEEK: SeekScraper,  # Add Seek to the scraper mapping
    }
    
    # 獲取增強版爬蟲映射並覆蓋基礎映射
    enhanced_mapping = EnhancedScraperConfig.get_enhanced_scraper_mapping()
    if enhanced_mapping:
        # 記錄增強版爬蟲狀態
        EnhancedScraperConfig.log_enhanced_status()
        
        # 更新映射
        if 'ziprecruiter' in enhanced_mapping:
            SCRAPER_MAPPING[Site.ZIP_RECRUITER] = enhanced_mapping['ziprecruiter']
        if 'google' in enhanced_mapping:
            SCRAPER_MAPPING[Site.GOOGLE] = enhanced_mapping['google']
        if 'bayt' in enhanced_mapping:
            SCRAPER_MAPPING[Site.BAYT] = enhanced_mapping['bayt']
    set_logger_level(verbose)
    job_type = get_enum_from_value(job_type) if job_type else None

    def get_site_type():
        site_types = list(Site)
        if isinstance(site_name, str):
            site_types = [map_str_to_site(site_name)]
        elif isinstance(site_name, Site):
            site_types = [site_name]
        elif isinstance(site_name, list):
            site_types = [
                map_str_to_site(site) if isinstance(site, str) else site
                for site in site_name
            ]
        return site_types

    country_enum = Country.from_string(country_indeed)

    scraper_input = ScraperInput(
        site_type=get_site_type(),
        country=country_enum,
        search_term=search_term,
        google_search_term=google_search_term,
        location=location,
        distance=distance,
        is_remote=is_remote,
        job_type=job_type,
        easy_apply=easy_apply,
        description_format=description_format,
        linkedin_fetch_description=linkedin_fetch_description,
        results_wanted=results_wanted,
        linkedin_company_ids=linkedin_company_ids,
        offset=offset,
        hours_old=hours_old,
    )

    def scrape_site(site: Site) -> Tuple[str, JobResponse]:
        scraper_class = SCRAPER_MAPPING[site]
        # BDJobs 不支援 user_agent 參數
        if site == Site.BDJOBS:
            scraper = scraper_class(proxies=proxies, ca_cert=ca_cert)
        else:
            scraper = scraper_class(proxies=proxies, ca_cert=ca_cert, user_agent=user_agent)
        scraped_data: JobResponse = scraper.scrape(scraper_input)
        cap_name = site.value.capitalize()
        site_name = "ZipRecruiter" if cap_name == "Zip_recruiter" else cap_name
        site_name = "LinkedIn" if cap_name == "Linkedin" else cap_name
        create_logger(site_name).info(f"finished scraping")
        return site.value, scraped_data

    site_to_jobs_dict = {}

    def worker(site):
        site_val, scraped_info = scrape_site(site)
        return site_val, scraped_info

    with ThreadPoolExecutor() as executor:
        future_to_site = {
            executor.submit(worker, site): site for site in scraper_input.site_type
        }

        for future in as_completed(future_to_site):
            site_value, scraped_data = future.result()
            site_to_jobs_dict[site_value] = scraped_data

    jobs_dfs: list[pd.DataFrame] = []

    for site, job_response in site_to_jobs_dict.items():
        for job in job_response.jobs:
            job_data = job.dict()
            job_url = job_data["job_url"]
            job_data["site"] = site
            job_data["company"] = job_data["company_name"]
            job_data["job_type"] = (
                ", ".join(job_type.value[0] for job_type in job_data["job_type"])
                if job_data["job_type"]
                else None
            )
            job_data["emails"] = (
                ", ".join(job_data["emails"]) if job_data["emails"] else None
            )
            if job_data["location"]:
                job_data["location"] = Location(
                    **job_data["location"]
                ).display_location()

            # Handle compensation
            compensation_obj = job_data.get("compensation")
            if compensation_obj and isinstance(compensation_obj, dict):
                job_data["interval"] = (
                    compensation_obj.get("interval").value
                    if compensation_obj.get("interval")
                    else None
                )
                job_data["min_amount"] = compensation_obj.get("min_amount")
                job_data["max_amount"] = compensation_obj.get("max_amount")
                job_data["currency"] = compensation_obj.get("currency", "USD")
                job_data["salary_source"] = SalarySource.DIRECT_DATA.value
                if enforce_annual_salary and (
                    job_data["interval"]
                    and job_data["interval"] != "yearly"
                    and job_data["min_amount"]
                    and job_data["max_amount"]
                ):
                    convert_to_annual(job_data)
            else:
                if country_enum == Country.USA:
                    (
                        job_data["interval"],
                        job_data["min_amount"],
                        job_data["max_amount"],
                        job_data["currency"],
                    ) = extract_salary(
                        job_data["description"],
                        enforce_annual_salary=enforce_annual_salary,
                    )
                    job_data["salary_source"] = SalarySource.DESCRIPTION.value

            job_data["salary_source"] = (
                job_data["salary_source"]
                if "min_amount" in job_data and job_data["min_amount"]
                else None
            )

            #naukri-specific fields
            job_data["skills"] = (
                ", ".join(job_data["skills"]) if job_data["skills"] else None
            )
            job_data["experience_range"] = job_data.get("experience_range")
            job_data["company_rating"] = job_data.get("company_rating")
            job_data["company_reviews_count"] = job_data.get("company_reviews_count")
            job_data["vacancy_count"] = job_data.get("vacancy_count")
            job_data["work_from_home_type"] = job_data.get("work_from_home_type")

            job_df = pd.DataFrame([job_data])
            jobs_dfs.append(job_df)

    if jobs_dfs:
        # Step 1: Filter out all-NA columns from each DataFrame before concatenation
        filtered_dfs = [df.dropna(axis=1, how="all") for df in jobs_dfs]

        # Step 2: Concatenate the filtered DataFrames
        jobs_df = pd.concat(filtered_dfs, ignore_index=True)

        # Step 3: Ensure all desired columns are present, adding missing ones as empty
        for column in desired_order:
            if column not in jobs_df.columns:
                jobs_df[column] = None  # Add missing columns as empty

        # Reorder the DataFrame according to the desired order
        jobs_df = jobs_df[desired_order]

        # Step 4: Sort the DataFrame as required
        return jobs_df.sort_values(
            by=["site", "date_posted"], ascending=[True, False]
        ).reset_index(drop=True)
    else:
        return pd.DataFrame()


# 非同步爬取函數
def scrape_jobs_async(
    site_name: str | list[str] | Site | list[Site] | None = None,
    search_term: str | None = None,
    location: str | None = None,
    distance: int | None = 50,
    is_remote: bool = False,
    job_type: str | None = None,
    easy_apply: bool | None = None,
    results_wanted: int = 15,
    country_indeed: str = "usa",
    proxies: list[str] | str | None = None,
    ca_cert: str | None = None,
    description_format: str = "markdown",
    linkedin_fetch_description: bool | None = False,
    linkedin_company_ids: list[int] | None = None,
    offset: int | None = 0,
    hours_old: int = None,
    enforce_annual_salary: bool = False,
    verbose: int = 0,
    user_agent: str = None,
    # 非同步特定參數
    async_config: Optional[AsyncConfig] = None,
    max_concurrent_requests: int = 5,
    request_delay: float = 1.0,
    enable_caching: bool = True,
    enable_quality_check: bool = True,
    **kwargs,
) -> pd.DataFrame:
    """
    非同步爬取職位資料
    
    Args:
        site_name: 網站名稱或網站列表
        search_term: 搜尋關鍵字
        location: 地點
        distance: 距離範圍
        is_remote: 是否遠程工作
        job_type: 工作類型
        easy_apply: 是否簡易申請
        results_wanted: 期望結果數量
        country_indeed: Indeed 國家設定
        proxies: 代理伺服器
        ca_cert: CA 證書
        description_format: 描述格式
        linkedin_fetch_description: 是否獲取 LinkedIn 描述
        linkedin_company_ids: LinkedIn 公司 ID 列表
        offset: 偏移量
        hours_old: 小時數限制
        enforce_annual_salary: 是否強制年薪
        verbose: 詳細程度
        user_agent: 用戶代理
        async_config: 非同步配置
        max_concurrent_requests: 最大並發請求數
        request_delay: 請求延遲
        enable_caching: 是否啟用快取
        enable_quality_check: 是否啟用品質檢查
        **kwargs: 其他參數
    
    Returns:
        包含職位資料的 Pandas DataFrame
    """
    
    # 設定日誌級別
    set_logger_level(verbose)
    
    # 準備網站列表
    def get_site_type():
        site_types = list(Site)
        if isinstance(site_name, str):
            site_types = [map_str_to_site(site_name)]
        elif isinstance(site_name, Site):
            site_types = [site_name]
        elif isinstance(site_name, list):
            site_types = [
                map_str_to_site(site) if isinstance(site, str) else site
                for site in site_name
            ]
        return site_types
    
    sites = get_site_type()
    
    # 創建非同步配置
    if async_config is None:
        async_config = AsyncConfig(
            mode=AsyncMode.THREADED,
            max_concurrent_requests=max_concurrent_requests,
            request_delay=request_delay,
            enable_caching=enable_caching,
            enable_quality_check=enable_quality_check,
            enable_monitoring=True
        )
    
    # 執行非同步爬取
    async def _run_async_scrape():
        # 獲取全域管理器
        manager = get_global_async_manager()
        manager.config = async_config
        
        # 註冊所有爬蟲
        SCRAPER_MAPPING = {
            Site.LINKEDIN: LinkedIn,
            Site.INDEED: Indeed,
            Site.ZIP_RECRUITER: ZipRecruiter,
            Site.GLASSDOOR: Glassdoor,
            Site.GOOGLE: Google,
            Site.BAYT: BaytScraper,
            Site.NAUKRI: Naukri,
            Site.BDJOBS: BDJobs,
            Site.SEEK: SeekScraper,
        }
        
        for site, scraper_class in SCRAPER_MAPPING.items():
            if site in sites:
                # BDJobs 不支援 user_agent 參數
                if site == Site.BDJOBS:
                    manager.register_sync_scraper(
                        site, scraper_class,
                        proxies=proxies,
                        ca_cert=ca_cert
                    )
                else:
                    manager.register_sync_scraper(
                        site, scraper_class,
                        proxies=proxies,
                        ca_cert=ca_cert,
                        user_agent=user_agent
                    )
        
        # 執行爬取
        results = await _async_scrape_jobs(
            sites=sites,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            job_type=job_type,
            is_remote=is_remote,
            config=async_config,
            distance=distance,
            easy_apply=easy_apply,
            country_indeed=country_indeed,
            description_format=description_format,
            linkedin_fetch_description=linkedin_fetch_description,
            linkedin_company_ids=linkedin_company_ids,
            offset=offset,
            hours_old=hours_old,
            **kwargs
        )
        
        return results
    
    # 運行非同步爬取
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    async_results = loop.run_until_complete(_run_async_scrape())
    
    # 轉換結果為 DataFrame
    return _convert_async_results_to_dataframe(
        async_results, enforce_annual_salary, Country.from_string(country_indeed)
    )


def _convert_async_results_to_dataframe(
    async_results: Dict[Site, AsyncScrapingResult],
    enforce_annual_salary: bool,
    country_enum: Country
) -> pd.DataFrame:
    """
    將非同步爬取結果轉換為 DataFrame
    
    Args:
        async_results: 非同步爬取結果字典
        enforce_annual_salary: 是否強制年薪
        country_enum: 國家枚舉
    
    Returns:
        包含職位資料的 Pandas DataFrame
    """
    jobs_dfs: list[pd.DataFrame] = []
    
    for site, result in async_results.items():
        if not result.success or not result.job_response:
            continue
        
        for job in result.job_response.jobs:
            job_data = job.dict()
            job_data["site"] = site.value
            job_data["company"] = job_data["company_name"]
            job_data["job_type"] = (
                ", ".join(job_type.value[0] for job_type in job_data["job_type"])
                if job_data["job_type"]
                else None
            )
            job_data["emails"] = (
                ", ".join(job_data["emails"]) if job_data["emails"] else None
            )
            
            if job_data["location"]:
                job_data["location"] = Location(
                    **job_data["location"]
                ).display_location()
            
            # 處理薪資資訊
            compensation_obj = job_data.get("compensation")
            if compensation_obj and isinstance(compensation_obj, dict):
                job_data["interval"] = (
                    compensation_obj.get("interval").value
                    if compensation_obj.get("interval")
                    else None
                )
                job_data["min_amount"] = compensation_obj.get("min_amount")
                job_data["max_amount"] = compensation_obj.get("max_amount")
                job_data["currency"] = compensation_obj.get("currency", "USD")
                job_data["salary_source"] = SalarySource.DIRECT_DATA.value
                
                if enforce_annual_salary and (
                    job_data["interval"]
                    and job_data["interval"] != "yearly"
                    and job_data["min_amount"]
                    and job_data["max_amount"]
                ):
                    convert_to_annual(job_data)
            else:
                if country_enum == Country.USA:
                    (
                        job_data["interval"],
                        job_data["min_amount"],
                        job_data["max_amount"],
                        job_data["currency"],
                    ) = extract_salary(
                        job_data["description"],
                        enforce_annual_salary=enforce_annual_salary,
                    )
                    job_data["salary_source"] = SalarySource.DESCRIPTION.value
            
            job_data["salary_source"] = (
                job_data["salary_source"]
                if "min_amount" in job_data and job_data["min_amount"]
                else None
            )
            
            # Naukri 特定欄位
            job_data["skills"] = (
                ", ".join(job_data["skills"]) if job_data["skills"] else None
            )
            job_data["experience_range"] = job_data.get("experience_range")
            job_data["company_rating"] = job_data.get("company_rating")
            job_data["company_reviews_count"] = job_data.get("company_reviews_count")
            job_data["vacancy_count"] = job_data.get("vacancy_count")
            job_data["work_from_home_type"] = job_data.get("work_from_home_type")
            
            job_df = pd.DataFrame([job_data])
            jobs_dfs.append(job_df)
    
    if jobs_dfs:
        # 過濾空列並合併
        filtered_dfs = [df.dropna(axis=1, how="all") for df in jobs_dfs]
        jobs_df = pd.concat(filtered_dfs, ignore_index=True)
        
        # 確保所有期望的列都存在
        for column in desired_order:
            if column not in jobs_df.columns:
                jobs_df[column] = None
        
        # 重新排序列
        jobs_df = jobs_df[desired_order]
        
        # 排序
        return jobs_df.sort_values(
            by=["site", "date_posted"], ascending=[True, False]
        ).reset_index(drop=True)
    else:
        return pd.DataFrame()


# 便利函數：創建非同步配置
def create_async_config(
    mode: AsyncMode = AsyncMode.THREADED,
    max_concurrent_requests: int = 5,
    request_delay: float = 1.0,
    timeout: float = 30.0,
    enable_caching: bool = True,
    enable_quality_check: bool = True,
    enable_monitoring: bool = True,
    retry_attempts: int = 3,
    **kwargs
) -> AsyncConfig:
    """
    創建非同步配置
    
    Args:
        mode: 非同步模式
        max_concurrent_requests: 最大並發請求數
        request_delay: 請求延遲（秒）
        timeout: 超時時間（秒）
        enable_caching: 是否啟用快取
        enable_quality_check: 是否啟用品質檢查
        enable_monitoring: 是否啟用監控
        retry_attempts: 重試次數
        **kwargs: 其他參數
    
    Returns:
        AsyncConfig 實例
    """
    return AsyncConfig(
        mode=mode,
        max_concurrent_requests=max_concurrent_requests,
        request_delay=request_delay,
        timeout=timeout,
        enable_caching=enable_caching,
        enable_quality_check=enable_quality_check,
        enable_monitoring=enable_monitoring,
        retry_attempts=retry_attempts,
        **kwargs
    )


# 更新 __all__ 導出
__all__ = [
    # 原有的類別
    "BDJobs",
    "Indeed",
    "LinkedIn",
    "Glassdoor",
    "Google",
    "ZipRecruiter",
    "BaytScraper",
    "Naukri",
    "SeekScraper",
    
    # 主要函數
    "scrape_jobs",
    "scrape_jobs_async",
    
    # 模型類別
    "Site",
    "JobType",
    "Country",
    "ScraperInput",
    "JobResponse",
    
    # 非同步相關
    "AsyncConfig",
    "AsyncMode",
    "AsyncScrapingManager",
    "create_async_config",
    "get_global_async_manager",
    
    # 工具函數
    "set_logger_level",
    "create_logger",
    "map_str_to_site",
]
