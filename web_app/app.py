#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 網頁應用
提供簡單易用的網頁界面，讓一般民眾無需程式設計知識即可使用職位搜尋功能

功能:
1. 網頁界面 - 簡潔的搜尋表單
2. API 端點 - RESTful API 支援
3. 即時搜尋 - AJAX 支援的動態搜尋
4. 結果展示 - 美觀的職位列表和詳細資訊
5. 下載功能 - CSV 和 JSON 格式下載

Author: jobseeker Team
Date: 2025-01-27
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
import pandas as pd

# 導入 jobseeker 核心功能
try:
    from jobseeker.route_manager import smart_scrape_jobs
    from jobseeker.model import Site, Country
except ImportError as e:
    print(f"警告: 無法導入 jobseeker 模組: {e}")
    print("請確保已正確安裝 jobseeker 套件")
    sys.exit(1)

# 創建 Flask 應用
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jobseeker-web-app-secret-key-2025')

# 啟用 CORS 支援
CORS(app)

# 配置
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB 最大上傳大小
    UPLOAD_FOLDER=project_root / 'web_app' / 'downloads',
    TEMPLATES_AUTO_RELOAD=True,
    DEBUG=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
)

# 確保下載目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全域變數儲存搜尋結果
search_results_cache = {}


@app.route('/')
def index():
    """
    首頁 - 顯示搜尋表單
    """
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_jobs():
    """
    執行職位搜尋
    
    接受 JSON 或表單數據
    返回搜尋結果的 JSON 響應
    """
    try:
        # 獲取請求數據
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # 提取搜尋參數
        user_query = data.get('query', '').strip()
        location = data.get('location', '').strip()
        results_wanted = int(data.get('results_wanted', 20))
        hours_old = data.get('hours_old')
        
        # 驗證輸入
        if not user_query:
            return jsonify({
                'success': False,
                'error': '請輸入搜尋關鍵字'
            }), 400
        
        if results_wanted < 1 or results_wanted > 100:
            return jsonify({
                'success': False,
                'error': '搜尋結果數量必須在 1-100 之間'
            }), 400
        
        # 處理時間限制
        if hours_old:
            try:
                hours_old = int(hours_old)
                if hours_old < 1:
                    hours_old = None
            except (ValueError, TypeError):
                hours_old = None
        
        # 生成搜尋 ID
        search_id = str(uuid.uuid4())
        
        # 執行智能搜尋
        print(f"開始搜尋: {user_query}")
        result = smart_scrape_jobs(
            user_query=user_query,
            location=location if location else None,
            results_wanted=results_wanted,
            hours_old=hours_old
        )
        
        # 處理搜尋結果
        if result.total_jobs == 0:
            return jsonify({
                'success': True,
                'search_id': search_id,
                'total_jobs': 0,
                'message': '未找到符合條件的職位，請嘗試調整搜尋條件',
                'jobs': [],
                'routing_info': {
                    'successful_agents': [agent.value for agent in result.successful_agents],
                    'confidence_score': result.routing_decision.confidence_score
                }
            })
        
        # 轉換職位數據為字典格式
        jobs_list = []
        if result.combined_jobs_data is not None:
            # 處理 NaN 值和數據類型
            df_clean = result.combined_jobs_data.fillna('')
            
            for _, row in df_clean.iterrows():
                job_dict = {
                    'title': str(row.get('title', '')),
                    'company': str(row.get('company', '')),
                    'location': str(row.get('location', '')),
                    'description': str(row.get('description', ''))[:500] + ('...' if len(str(row.get('description', ''))) > 500 else ''),
                    'salary_min': float(row['salary_min']) if pd.notna(row.get('salary_min')) else None,
                    'salary_max': float(row['salary_max']) if pd.notna(row.get('salary_max')) else None,
                    'salary_currency': str(row.get('salary_currency', '')),
                    'date_posted': str(row.get('date_posted', '')),
                    'job_url': str(row.get('job_url', '')),
                    'job_url_direct': str(row.get('job_url_direct', '')),
                    'site': str(row.get('site', '')),
                    'job_type': str(row.get('job_type', '')),
                    'is_remote': bool(row.get('is_remote', False))
                }
                jobs_list.append(job_dict)
        
        # 快取搜尋結果
        search_results_cache[search_id] = {
            'result': result,
            'timestamp': datetime.now(),
            'query': user_query,
            'location': location
        }
        
        # 返回成功響應
        return jsonify({
            'success': True,
            'search_id': search_id,
            'total_jobs': result.total_jobs,
            'jobs': jobs_list,
            'routing_info': {
                'successful_agents': [agent.value for agent in result.successful_agents],
                'failed_agents': [agent.value for agent in result.failed_agents],
                'confidence_score': result.routing_decision.confidence_score,
                'execution_time': result.total_execution_time
            },
            'search_params': {
                'query': user_query,
                'location': location,
                'results_wanted': results_wanted,
                'hours_old': hours_old
            }
        })
        
    except Exception as e:
        print(f"搜尋錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'搜尋過程中發生錯誤: {str(e)}'
        }), 500


@app.route('/download/<search_id>/<format>')
def download_results(search_id, format):
    """
    下載搜尋結果
    
    Args:
        search_id: 搜尋 ID
        format: 下載格式 (csv, json)
    """
    try:
        # 檢查搜尋結果是否存在
        if search_id not in search_results_cache:
            flash('搜尋結果不存在或已過期', 'error')
            return redirect(url_for('index'))
        
        cached_result = search_results_cache[search_id]
        result = cached_result['result']
        
        if result.combined_jobs_data is None or result.total_jobs == 0:
            flash('沒有可下載的搜尋結果', 'warning')
            return redirect(url_for('index'))
        
        # 生成檔案名稱
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        query_safe = ''.join(c for c in cached_result['query'][:20] if c.isalnum() or c in (' ', '-', '_')).strip()
        
        if format.lower() == 'csv':
            filename = f"jobseeker_{query_safe}_{timestamp}.csv"
            filepath = app.config['UPLOAD_FOLDER'] / filename
            
            # 轉換為標準格式
            standardized_data = convert_to_standard_format(result.combined_jobs_data)
            
            # 儲存 CSV 檔案
            standardized_data.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
            
        elif format.lower() == 'json':
            filename = f"jobseeker_{query_safe}_{timestamp}.json"
            filepath = app.config['UPLOAD_FOLDER'] / filename
            
            # 轉換為 JSON 格式
            jobs_data = result.combined_jobs_data.fillna('').to_dict('records')
            
            export_data = {
                'search_info': {
                    'query': cached_result['query'],
                    'location': cached_result['location'],
                    'timestamp': cached_result['timestamp'].isoformat(),
                    'total_jobs': result.total_jobs
                },
                'routing_info': {
                    'successful_agents': [agent.value for agent in result.successful_agents],
                    'failed_agents': [agent.value for agent in result.failed_agents],
                    'confidence_score': result.routing_decision.confidence_score,
                    'execution_time': result.total_execution_time
                },
                'jobs': jobs_data
            }
            
            # 儲存 JSON 檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
        
        else:
            flash('不支援的下載格式', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"下載錯誤: {e}")
        flash(f'下載失敗: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/demo')
def demo_results():
    """
    展示測試結果頁面
    """
    return render_template('demo_results.html')


@app.route('/api/sites')
def get_supported_sites():
    """
    獲取支援的求職網站列表
    """
    try:
        sites = [{
            'value': site.value,
            'name': site.value.title(),
            'description': get_site_description(site)
        } for site in Site]
        
        return jsonify({
            'success': True,
            'sites': sites
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/countries')
def get_supported_countries():
    """
    獲取支援的國家列表
    """
    try:
        countries = [{
            'value': country.value[0],  # 國家名稱
            'code': country.value[1],   # 國家代碼
            'name': country.name
        } for country in Country]
        
        return jsonify({
            'success': True,
            'countries': countries
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """
    健康檢查端點
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


def convert_to_standard_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    轉換職位數據為標準格式
    按照用戶指定的格式：SITE, TITLE, COMPANY, CITY, STATE, JOB_TYPE, INTERVAL, MIN_AMOUNT, MAX_AMOUNT, JOB_URL, DESCRIPTION
    
    Args:
        df: 原始職位數據 DataFrame
        
    Returns:
        標準化的 DataFrame
    """
    # 創建標準化的 DataFrame
    standardized_df = pd.DataFrame()
    
    # 按照標準格式映射欄位
    standardized_df['SITE'] = df.get('site', '').fillna('')
    standardized_df['TITLE'] = df.get('title', '').fillna('')
    standardized_df['COMPANY'] = df.get('company', '').fillna('')
    
    # 處理地點資訊 - 分離城市和州/省
    location = df.get('location', '').fillna('')
    standardized_df['CITY'] = location.apply(extract_city)
    standardized_df['STATE'] = location.apply(extract_state)
    
    standardized_df['JOB_TYPE'] = df.get('job_type', '').fillna('')
    standardized_df['INTERVAL'] = df.get('interval', '').fillna('')
    standardized_df['MIN_AMOUNT'] = df.get('min_amount', '').fillna('')
    standardized_df['MAX_AMOUNT'] = df.get('max_amount', '').fillna('')
    standardized_df['JOB_URL'] = df.get('job_url', '').fillna('')
    standardized_df['DESCRIPTION'] = df.get('description', '').fillna('')
    
    return standardized_df


def extract_city(location_str):
    """
    從地點字串中提取城市名稱
    
    Args:
        location_str: 地點字串
        
    Returns:
        城市名稱
    """
    if pd.isna(location_str) or location_str == '':
        return ''
    
    # 分割地點字串，通常格式為 "City, State" 或 "City"
    parts = str(location_str).split(',')
    return parts[0].strip() if parts else ''


def extract_state(location_str):
    """
    從地點字串中提取州/省名稱
    
    Args:
        location_str: 地點字串
        
    Returns:
        州/省名稱
    """
    if pd.isna(location_str) or location_str == '':
        return ''
    
    # 分割地點字串，通常格式為 "City, State" 或 "City"
    parts = str(location_str).split(',')
    return parts[1].strip() if len(parts) > 1 else ''


def get_site_description(site: Site) -> str:
    """
    獲取求職網站描述
    
    Args:
        site: Site 枚舉值
        
    Returns:
        網站描述字串
    """
    descriptions = {
        'indeed': '全球最大的求職網站，涵蓋各行各業',
        'linkedin': '專業人脈網站，適合白領和管理職位',
        'glassdoor': '提供公司評價和薪資資訊',
        'seek': '澳洲和紐西蘭最大的求職網站',
        'ziprecruiter': '美國知名求職網站，AI 智能匹配',
        'google': 'Google 職位搜尋，整合多個平台',
        'naukri': '印度最大的求職網站',
        'bayt': '中東地區領先的求職平台',
        'bdjobs': '孟加拉國本地求職網站'
    }
    
    return descriptions.get(site.value, f'{site.value.title()} 求職網站')


if __name__ == '__main__':
    print("🚀 jobseeker 網頁應用啟動中...")
    print("📱 訪問 http://localhost:5000 開始使用")
    print("📊 API 文檔: http://localhost:5000/api/sites")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config['DEBUG']
    )