#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版 API 系統
提供分頁、過濾、排序和搜索功能

Author: jobseeker Team
Date: 2025-01-27
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import math

from flask import Blueprint, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc, func, or_, and_

from .models import SearchResult, Favorite, User


class SortOrder(Enum):
    """排序順序"""
    ASC = "asc"
    DESC = "desc"


class SortField(Enum):
    """排序欄位"""
    DATE_POSTED = "date_posted"
    TITLE = "title"
    COMPANY = "company"
    LOCATION = "location"
    SALARY = "salary"
    RELEVANCE = "relevance"


@dataclass
class PaginationParams:
    """分頁參數"""
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100
    
    def __post_init__(self):
        # 確保參數在合理範圍內
        self.page = max(1, self.page)
        self.per_page = min(max(1, self.per_page), self.max_per_page)


@dataclass
class SortParams:
    """排序參數"""
    field: SortField = SortField.RELEVANCE
    order: SortOrder = SortOrder.DESC


@dataclass
class FilterParams:
    """過濾參數"""
    sites: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    job_types: Optional[List[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    keywords: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    is_remote: Optional[bool] = None


@dataclass
class SearchParams:
    """搜尋參數"""
    query: Optional[str] = None
    location: Optional[str] = None
    site: Optional[str] = None
    country: Optional[str] = None
    results_wanted: int = 50
    hours_old: Optional[int] = None


@dataclass
class PaginatedResponse:
    """分頁響應"""
    data: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    filters: Dict[str, Any]
    sort: Dict[str, Any]
    search_info: Dict[str, Any]
    metadata: Dict[str, Any]


class EnhancedAPIManager:
    """增強版 API 管理器"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.logger = current_app.logger
    
    def parse_pagination_params(self) -> PaginationParams:
        """解析分頁參數"""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            max_per_page = int(request.args.get('max_per_page', 100))
            
            return PaginationParams(
                page=page,
                per_page=per_page,
                max_per_page=max_per_page
            )
        except (ValueError, TypeError):
            return PaginationParams()
    
    def parse_sort_params(self) -> SortParams:
        """解析排序參數"""
        try:
            sort_field = request.args.get('sort', 'relevance')
            sort_order = request.args.get('order', 'desc')
            
            # 驗證排序欄位
            try:
                field = SortField(sort_field)
            except ValueError:
                field = SortField.RELEVANCE
            
            # 驗證排序順序
            try:
                order = SortOrder(sort_order)
            except ValueError:
                order = SortOrder.DESC
            
            return SortParams(field=field, order=order)
        except Exception:
            return SortParams()
    
    def parse_filter_params(self) -> FilterParams:
        """解析過濾參數"""
        try:
            # 解析列表參數
            def parse_list_param(param_name: str) -> Optional[List[str]]:
                value = request.args.get(param_name)
                if value:
                    return [item.strip() for item in value.split(',') if item.strip()]
                return None
            
            # 解析數值參數
            def parse_float_param(param_name: str) -> Optional[float]:
                value = request.args.get(param_name)
                if value:
                    try:
                        return float(value)
                    except ValueError:
                        return None
                return None
            
            # 解析布林參數
            def parse_bool_param(param_name: str) -> Optional[bool]:
                value = request.args.get(param_name)
                if value:
                    return value.lower() in ['true', '1', 'yes', 'on']
                return None
            
            return FilterParams(
                sites=parse_list_param('sites'),
                countries=parse_list_param('countries'),
                job_types=parse_list_param('job_types'),
                salary_min=parse_float_param('salary_min'),
                salary_max=parse_float_param('salary_max'),
                date_from=request.args.get('date_from'),
                date_to=request.args.get('date_to'),
                keywords=parse_list_param('keywords'),
                companies=parse_list_param('companies'),
                locations=parse_list_param('locations'),
                is_remote=parse_bool_param('is_remote')
            )
        except Exception:
            return FilterParams()
    
    def parse_search_params(self) -> SearchParams:
        """解析搜尋參數"""
        try:
            return SearchParams(
                query=request.args.get('q') or request.args.get('query'),
                location=request.args.get('location'),
                site=request.args.get('site'),
                country=request.args.get('country'),
                results_wanted=int(request.args.get('results_wanted', 50)),
                hours_old=int(request.args.get('hours_old')) if request.args.get('hours_old') else None
            )
        except (ValueError, TypeError):
            return SearchParams()
    
    def apply_filters(self, query, filters: FilterParams):
        """應用過濾條件"""
        # 網站過濾
        if filters.sites:
            query = query.filter(SearchResult.site.in_(filters.sites))
        
        # 國家過濾
        if filters.countries:
            query = query.filter(SearchResult.country.in_(filters.countries))
        
        # 職位類型過濾
        if filters.job_types:
            # 這裡需要根據實際的數據結構來調整
            # 假設 job_type 存儲在 jobs JSON 欄位中
            conditions = []
            for job_type in filters.job_types:
                conditions.append(SearchResult.jobs.contains(f'"job_type": "{job_type}"'))
            if conditions:
                query = query.filter(or_(*conditions))
        
        # 薪資過濾
        if filters.salary_min is not None or filters.salary_max is not None:
            # 這裡需要根據實際的薪資數據結構來調整
            # 假設薪資信息存儲在 jobs JSON 欄位中
            if filters.salary_min is not None:
                query = query.filter(SearchResult.jobs.contains(f'"min_amount": {filters.salary_min}'))
            if filters.salary_max is not None:
                query = query.filter(SearchResult.jobs.contains(f'"max_amount": {filters.salary_max}'))
        
        # 日期過濾
        if filters.date_from:
            try:
                date_from = datetime.strptime(filters.date_from, '%Y-%m-%d')
                query = query.filter(SearchResult.created_at >= date_from)
            except ValueError:
                pass
        
        if filters.date_to:
            try:
                date_to = datetime.strptime(filters.date_to, '%Y-%m-%d')
                query = query.filter(SearchResult.created_at <= date_to)
            except ValueError:
                pass
        
        # 關鍵詞過濾
        if filters.keywords:
            conditions = []
            for keyword in filters.keywords:
                conditions.append(
                    or_(
                        SearchResult.query.contains(keyword),
                        SearchResult.jobs.contains(keyword)
                    )
                )
            if conditions:
                query = query.filter(or_(*conditions))
        
        # 公司過濾
        if filters.companies:
            conditions = []
            for company in filters.companies:
                conditions.append(SearchResult.jobs.contains(f'"company": "{company}"'))
            if conditions:
                query = query.filter(or_(*conditions))
        
        # 地點過濾
        if filters.locations:
            conditions = []
            for location in filters.locations:
                conditions.append(SearchResult.jobs.contains(f'"location": "{location}"'))
            if conditions:
                query = query.filter(or_(*conditions))
        
        # 遠程工作過濾
        if filters.is_remote is not None:
            if filters.is_remote:
                query = query.filter(SearchResult.jobs.contains('"is_remote": true'))
            else:
                query = query.filter(SearchResult.jobs.contains('"is_remote": false'))
        
        return query
    
    def apply_sorting(self, query, sort_params: SortParams):
        """應用排序"""
        if sort_params.field == SortField.DATE_POSTED:
            if sort_params.order == SortOrder.ASC:
                query = query.order_by(asc(SearchResult.created_at))
            else:
                query = query.order_by(desc(SearchResult.created_at))
        
        elif sort_params.field == SortField.TITLE:
            # 這裡需要根據實際的數據結構來調整
            # 假設標題存儲在 jobs JSON 欄位中
            if sort_params.order == SortOrder.ASC:
                query = query.order_by(asc(SearchResult.jobs))
            else:
                query = query.order_by(desc(SearchResult.jobs))
        
        elif sort_params.field == SortField.COMPANY:
            # 類似地處理公司排序
            if sort_params.order == SortOrder.ASC:
                query = query.order_by(asc(SearchResult.jobs))
            else:
                query = query.order_by(desc(SearchResult.jobs))
        
        elif sort_params.field == SortField.RELEVANCE:
            # 相關性排序（預設按創建時間倒序）
            query = query.order_by(desc(SearchResult.created_at))
        
        return query
    
    def get_paginated_results(self, 
                            pagination: PaginationParams,
                            sort_params: SortParams,
                            filters: FilterParams,
                            search_params: Optional[SearchParams] = None) -> PaginatedResponse:
        """獲取分頁結果"""
        try:
            # 基礎查詢
            query = SearchResult.query
            
            # 應用搜尋條件
            if search_params and search_params.query:
                query = query.filter(
                    or_(
                        SearchResult.query.contains(search_params.query),
                        SearchResult.jobs.contains(search_params.query)
                    )
                )
            
            if search_params and search_params.location:
                query = query.filter(SearchResult.jobs.contains(f'"location": "{search_params.location}"'))
            
            if search_params and search_params.site:
                query = query.filter(SearchResult.site == search_params.site)
            
            if search_params and search_params.country:
                query = query.filter(SearchResult.country == search_params.country)
            
            # 應用過濾條件
            query = self.apply_filters(query, filters)
            
            # 獲取總數
            total_count = query.count()
            
            # 應用排序
            query = self.apply_sorting(query, sort_params)
            
            # 計算分頁
            total_pages = math.ceil(total_count / pagination.per_page)
            offset = (pagination.page - 1) * pagination.per_page
            
            # 獲取分頁數據
            results = query.offset(offset).limit(pagination.per_page).all()
            
            # 轉換為字典格式
            data = []
            for result in results:
                try:
                    jobs_data = json.loads(result.jobs) if isinstance(result.jobs, str) else result.jobs
                except (json.JSONDecodeError, TypeError):
                    jobs_data = []
                
                data.append({
                    'id': result.id,
                    'query': result.query,
                    'site': result.site,
                    'country': result.country,
                    'location': result.location,
                    'jobs_count': len(jobs_data) if isinstance(jobs_data, list) else 0,
                    'jobs': jobs_data,
                    'created_at': result.created_at.isoformat(),
                    'execution_time': result.execution_time,
                    'success': result.success,
                    'error_message': result.error_message
                })
            
            # 構建分頁信息
            pagination_info = {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_prev': pagination.page > 1,
                'has_next': pagination.page < total_pages,
                'prev_page': pagination.page - 1 if pagination.page > 1 else None,
                'next_page': pagination.page + 1 if pagination.page < total_pages else None
            }
            
            # 構建過濾信息
            filters_info = asdict(filters)
            
            # 構建排序信息
            sort_info = {
                'field': sort_params.field.value,
                'order': sort_params.order.value
            }
            
            # 構建搜尋信息
            search_info = asdict(search_params) if search_params else {}
            
            # 構建元數據
            metadata = {
                'generated_at': datetime.now().isoformat(),
                'api_version': '2.0',
                'response_time': time.time()
            }
            
            return PaginatedResponse(
                data=data,
                pagination=pagination_info,
                filters=filters_info,
                sort=sort_info,
                search_info=search_info,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"獲取分頁結果失敗: {str(e)}")
            raise
    
    def get_aggregated_stats(self, filters: FilterParams) -> Dict[str, Any]:
        """獲取聚合統計"""
        try:
            query = SearchResult.query
            
            # 應用過濾條件
            query = self.apply_filters(query, filters)
            
            # 基本統計
            total_searches = query.count()
            successful_searches = query.filter(SearchResult.success == True).count()
            
            # 按網站統計
            site_stats = {}
            site_results = query.with_entities(
                SearchResult.site, 
                func.count(SearchResult.id).label('count'),
                func.avg(SearchResult.execution_time).label('avg_time')
            ).group_by(SearchResult.site).all()
            
            for site, count, avg_time in site_results:
                site_stats[site] = {
                    'count': count,
                    'avg_execution_time': float(avg_time) if avg_time else 0
                }
            
            # 按國家統計
            country_stats = {}
            country_results = query.with_entities(
                SearchResult.country,
                func.count(SearchResult.id).label('count')
            ).group_by(SearchResult.country).all()
            
            for country, count in country_results:
                country_stats[country] = {'count': count}
            
            # 時間統計
            time_stats = {}
            time_results = query.with_entities(
                func.date(SearchResult.created_at).label('date'),
                func.count(SearchResult.id).label('count')
            ).group_by(func.date(SearchResult.created_at)).order_by(desc('date')).limit(30).all()
            
            for date, count in time_results:
                time_stats[date.isoformat()] = {'count': count}
            
            return {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'success_rate': successful_searches / total_searches if total_searches > 0 else 0,
                'site_stats': site_stats,
                'country_stats': country_stats,
                'time_stats': time_stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"獲取聚合統計失敗: {str(e)}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """獲取搜尋建議"""
        try:
            if not query or len(query.strip()) < 2:
                return []
            
            # 從歷史搜尋中獲取建議
            suggestions = SearchResult.query.filter(
                SearchResult.query.contains(query.strip())
            ).with_entities(SearchResult.query).distinct().limit(limit).all()
            
            return [suggestion[0] for suggestion in suggestions]
            
        except Exception as e:
            self.logger.error(f"獲取搜尋建議失敗: {str(e)}")
            return []
    
    def get_available_filters(self) -> Dict[str, Any]:
        """獲取可用的過濾選項"""
        try:
            # 獲取所有網站
            sites = [site[0] for site in SearchResult.query.with_entities(SearchResult.site).distinct().all()]
            
            # 獲取所有國家
            countries = [country[0] for country in SearchResult.query.with_entities(SearchResult.country).distinct().all()]
            
            # 獲取所有地點（從 jobs 數據中提取）
            locations = set()
            results = SearchResult.query.with_entities(SearchResult.jobs).all()
            for result in results:
                try:
                    jobs_data = json.loads(result.jobs) if isinstance(result.jobs, str) else result.jobs
                    if isinstance(jobs_data, list):
                        for job in jobs_data:
                            if isinstance(job, dict) and 'location' in job:
                                location = job['location']
                                if isinstance(location, dict) and 'city' in location:
                                    locations.add(location['city'])
                                elif isinstance(location, str):
                                    locations.add(location)
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
            
            # 獲取所有公司（從 jobs 數據中提取）
            companies = set()
            for result in results:
                try:
                    jobs_data = json.loads(result.jobs) if isinstance(result.jobs, str) else result.jobs
                    if isinstance(jobs_data, list):
                        for job in jobs_data:
                            if isinstance(job, dict) and 'company' in job:
                                companies.add(job['company'])
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
            
            return {
                'sites': sorted(sites),
                'countries': sorted(countries),
                'locations': sorted(list(locations)),
                'companies': sorted(list(companies)),
                'job_types': ['full_time', 'part_time', 'contract', 'internship', 'temporary'],
                'sort_fields': [field.value for field in SortField],
                'sort_orders': [order.value for order in SortOrder],
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"獲取可用過濾選項失敗: {str(e)}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }


# 創建 Blueprint
enhanced_api_bp = Blueprint('enhanced_api', __name__, url_prefix='/api/v2')


@enhanced_api_bp.route('/search', methods=['GET'])
def enhanced_search():
    """增強版搜尋 API"""
    try:
        # 初始化 API 管理器
        from . import db
        api_manager = EnhancedAPIManager(db)
        
        # 解析參數
        pagination = api_manager.parse_pagination_params()
        sort_params = api_manager.parse_sort_params()
        filters = api_manager.parse_filter_params()
        search_params = api_manager.parse_search_params()
        
        # 獲取分頁結果
        result = api_manager.get_paginated_results(
            pagination, sort_params, filters, search_params
        )
        
        return jsonify(asdict(result))
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '搜尋失敗'
        }), 500


@enhanced_api_bp.route('/search/stats', methods=['GET'])
def search_stats():
    """搜尋統計 API"""
    try:
        from . import db
        api_manager = EnhancedAPIManager(db)
        
        filters = api_manager.parse_filter_params()
        stats = api_manager.get_aggregated_stats(filters)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '獲取統計失敗'
        }), 500


@enhanced_api_bp.route('/search/suggestions', methods=['GET'])
def search_suggestions():
    """搜尋建議 API"""
    try:
        from . import db
        api_manager = EnhancedAPIManager(db)
        
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        suggestions = api_manager.get_search_suggestions(query, limit)
        
        return jsonify({
            'suggestions': suggestions,
            'query': query,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '獲取建議失敗'
        }), 500


@enhanced_api_bp.route('/filters', methods=['GET'])
def available_filters():
    """可用過濾選項 API"""
    try:
        from . import db
        api_manager = EnhancedAPIManager(db)
        
        filters = api_manager.get_available_filters()
        
        return jsonify(filters)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '獲取過濾選項失敗'
        }), 500


@enhanced_api_bp.route('/search/<search_id>', methods=['GET'])
def get_search_by_id(search_id: str):
    """根據 ID 獲取搜尋結果"""
    try:
        from . import db
        
        result = SearchResult.query.filter_by(id=search_id).first()
        if not result:
            return jsonify({
                'error': '搜尋結果不存在',
                'search_id': search_id
            }), 404
        
        try:
            jobs_data = json.loads(result.jobs) if isinstance(result.jobs, str) else result.jobs
        except (json.JSONDecodeError, TypeError):
            jobs_data = []
        
        return jsonify({
            'id': result.id,
            'query': result.query,
            'site': result.site,
            'country': result.country,
            'location': result.location,
            'jobs_count': len(jobs_data) if isinstance(jobs_data, list) else 0,
            'jobs': jobs_data,
            'created_at': result.created_at.isoformat(),
            'execution_time': result.execution_time,
            'success': result.success,
            'error_message': result.error_message,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '獲取搜尋結果失敗'
        }), 500


@enhanced_api_bp.route('/search/<search_id>/jobs', methods=['GET'])
def get_jobs_by_search_id(search_id: str):
    """根據搜尋 ID 獲取職位列表（支援分頁）"""
    try:
        from . import db
        api_manager = EnhancedAPIManager(db)
        
        # 獲取搜尋結果
        result = SearchResult.query.filter_by(id=search_id).first()
        if not result:
            return jsonify({
                'error': '搜尋結果不存在',
                'search_id': search_id
            }), 404
        
        try:
            jobs_data = json.loads(result.jobs) if isinstance(result.jobs, str) else result.jobs
        except (json.JSONDecodeError, TypeError):
            jobs_data = []
        
        if not isinstance(jobs_data, list):
            jobs_data = []
        
        # 解析分頁參數
        pagination = api_manager.parse_pagination_params()
        
        # 計算分頁
        total_count = len(jobs_data)
        total_pages = math.ceil(total_count / pagination.per_page)
        offset = (pagination.page - 1) * pagination.per_page
        
        # 獲取分頁數據
        paginated_jobs = jobs_data[offset:offset + pagination.per_page]
        
        # 構建響應
        return jsonify({
            'search_id': search_id,
            'jobs': paginated_jobs,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_prev': pagination.page > 1,
                'has_next': pagination.page < total_pages,
                'prev_page': pagination.page - 1 if pagination.page > 1 else None,
                'next_page': pagination.page + 1 if pagination.page < total_pages else None
            },
            'search_info': {
                'query': result.query,
                'site': result.site,
                'country': result.country,
                'location': result.location,
                'created_at': result.created_at.isoformat()
            },
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '獲取職位列表失敗'
        }), 500


@enhanced_api_bp.route('/export/<search_id>', methods=['GET'])
def export_search_results(search_id: str):
    """導出搜尋結果"""
    try:
        from . import db
        
        result = SearchResult.query.filter_by(id=search_id).first()
        if not result:
            return jsonify({
                'error': '搜尋結果不存在',
                'search_id': search_id
            }), 404
        
        try:
            jobs_data = json.loads(result.jobs) if isinstance(result.jobs, str) else result.jobs
        except (json.JSONDecodeError, TypeError):
            jobs_data = []
        
        format_type = request.args.get('format', 'json').lower()
        
        if format_type == 'csv':
            # CSV 格式導出
            import pandas as pd
            from io import StringIO
            
            if not jobs_data:
                return jsonify({'error': '沒有數據可導出'}), 400
            
            # 轉換為 DataFrame
            df = pd.DataFrame(jobs_data)
            
            # 創建 CSV
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            
            from flask import make_response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=search_{search_id}.csv'
            
            return response
            
        else:
            # JSON 格式導出
            return jsonify({
                'search_id': search_id,
                'query': result.query,
                'site': result.site,
                'country': result.country,
                'location': result.location,
                'created_at': result.created_at.isoformat(),
                'jobs': jobs_data,
                'exported_at': datetime.now().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '導出失敗'
        }), 500
