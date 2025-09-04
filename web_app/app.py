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
# 支援本地開發和 Railway 部署環境
project_root = Path(__file__).parent.parent
if project_root.name == 'web_app':  # Railway 部署時的情況
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import time
from flask_cors import CORS
import pandas as pd

# 導入 jobseeker 核心功能
try:
    from jobseeker.smart_router import smart_router
    from jobseeker.model import Site, Country
    from jobseeker.query_parser import parse_user_query_smart
    from jobseeker.intent_analyzer import analyze_user_intent, is_job_related
    from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer
    from jobseeker.intelligent_decision_engine import DecisionResult, ProcessingStrategy, PlatformSelectionMode
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
    DEBUG=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{project_root / 'web_app' / 'db' / 'app.db'}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# 確保下載目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(project_root / 'web_app' / 'db', exist_ok=True)

# 全域變數儲存搜尋結果
search_results_cache = {}

# 初始化LLM意圖分析器
# 嘗試使用真實的LLM提供商，如果沒有API密鑰則回退到模擬模式
try:
    from jobseeker.llm_intent_analyzer import LLMProvider
    
    # 檢查是否有OpenAI API密鑰
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        llm_intent_analyzer = LLMIntentAnalyzer(
            provider=LLMProvider.OPENAI_GPT35,
            api_key=openai_api_key,
            fallback_to_basic=True
        )
        print("✅ LLM意圖分析器已啟用 - 使用OpenAI GPT-3.5")
    else:
        # 沒有API密鑰，使用模擬模式
        llm_intent_analyzer = LLMIntentAnalyzer(
            provider=LLMProvider.OPENAI_GPT35,  # 提供商設置但沒有API密鑰會自動回退到模擬
            api_key=None,
            fallback_to_basic=True
        )
        print("⚠️  LLM意圖分析器使用模擬模式 - 請設置OPENAI_API_KEY環境變量以啟用真實LLM")
except Exception as e:
    # 如果導入失敗，使用默認初始化
    llm_intent_analyzer = LLMIntentAnalyzer()
    print(f"⚠️  LLM意圖分析器初始化失敗，使用默認模式: {e}")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(512))
    company = db.Column(db.String(512))
    location = db.Column(db.String(512))
    site = db.Column(db.String(64))
    job_url = db.Column(db.String(1024))
    job_url_direct = db.Column(db.String(1024))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('favorites', lazy=True))


class TestRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    total = db.Column(db.Integer, default=0)
    passed = db.Column(db.Integer, default=0)
    failed = db.Column(db.Integer, default=0)
    skipped = db.Column(db.Integer, default=0)
    duration_sec = db.Column(db.Float, default=0.0)


class TestCaseResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('test_run.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(16), nullable=False)  # pass/fail/skip
    duration_ms = db.Column(db.Integer, default=0)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    run = db.relationship('TestRun', backref=db.backref('cases', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    # API 請求返回 401 JSON，其餘導向登入頁
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': '未登入'}), 401
    flash('請先登入', 'warning')
    return redirect(url_for('login', next=request.url))


def is_admin_user() -> bool:
    if not current_user.is_authenticated:
        return False
    admin_emails = os.environ.get('ADMIN_EMAILS', '')
    allow = [e.strip().lower() for e in admin_emails.split(',') if e.strip()]
    if not allow:
        # Default: no admins unless explicitly configured
        return False
    return current_user.email.lower() in allow


def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return unauthorized()
        if not is_admin_user():
            flash('需要管理員權限', 'error')
            return redirect(url_for('index'))
        return fn(*args, **kwargs)
    return wrapper

# 初始化資料庫
with app.app_context():
    db.create_all()

@app.context_processor
def inject_global_flags():
    return {'is_admin': is_admin_user()}

@app.route('/')
def index():
    """
    首頁 - 顯示搜尋表單
    """
    return render_template('index.html')


@app.route('/debug')
def debug_test():
    """
    調試測試頁面
    """
    return render_template('debug_test.html')


@app.route('/search', methods=['POST'])
def search_jobs():
    """
    執行職位搜尋 (支援分頁)
    
    接受 JSON 或表單數據
    返回搜尋結果的 JSON 響應，包含分頁資訊
    """
    try:
        # 獲取請求數據
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # 提取搜尋參數（單欄輸入，地點可由解析得出）
        user_query = data.get('query', '').strip()
        location = data.get('location', '').strip() if data.get('location') is not None else ''
        results_wanted = int(data.get('results_wanted', 20))
        hours_old = data.get('hours_old')
        selected_sites = data.get('selected_sites', '')
        
        # 新增分頁參數
        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 20))
        
        # 驗證分頁參數
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        # 解析單欄查詢（LLM-ready 規則式解析）
        parsed = parse_user_query_smart(user_query)

        # 若未顯式提供地點，使用解析到的地點
        derived_location = location if location else (parsed.location or '')

        # 嘗試推斷國家（供 Indeed/Glassdoor 等域名選擇）
        derived_country = None
        try:
            if parsed.location:
                # Country.from_string 支援英文關鍵詞，如 'australia','uk','usa','taiwan'
                derived_country = Country.from_string(parsed.location).value[0]
        except Exception:
            derived_country = None

        # 處理選擇的網站
        site_name = None
        if selected_sites:
            # 如果selected_sites是字符串，轉換為列表
            if isinstance(selected_sites, str):
                sites_list = [site.strip() for site in selected_sites.split(',') if site.strip()]
            else:
                # 如果已經是列表，直接使用
                sites_list = [site.strip() for site in selected_sites if site.strip()]
            
            if len(sites_list) == 1:
                # 如果只選擇了一個網站，使用該網站
                site_name = sites_list[0]
            elif len(sites_list) > 1:
                # 如果選擇了多個網站，使用智能路由但限制在選擇的網站內
                print(f"多平台搜尋: {sites_list}")
                # 保持 site_name 為 None，讓智能路由處理，但會通過 selected_sites 限制
            # 如果選擇了多個網站，保持 site_name 為 None（搜尋所有網站）
        elif parsed.site_hints and len(parsed.site_hints) == 1:
            # 使用查詢中的單一站點提示
            site_name = parsed.site_hints[0]
        
        # 驗證輸入
        if not user_query:
            return jsonify({
                'success': False,
                'error': '請輸入搜尋關鍵字'
            }), 400
        
        # 使用LLM智能意圖分析器進行分析和決策
        try:
            llm_intent_result, decision_result = llm_intent_analyzer.analyze_intent_with_decision(user_query)
            
            # 檢查是否為求職相關查詢
            if not llm_intent_result.is_job_related:
                return jsonify({
                    'success': False,
                    'error': llm_intent_result.rejection_message or '抱歉，我是AI助手，僅能協助您處理求職相關問題，無法進行一般聊天。',
                    'intent_analysis': {
                        'intent_type': llm_intent_result.intent_type.value if llm_intent_result.intent_type else 'unclear',
                        'confidence': llm_intent_result.confidence,
                        'analysis_method': 'llm' if llm_intent_result.llm_used else 'basic'
                    },
                    'decision_analysis': {
                        'strategy': decision_result.strategy.value if decision_result else 'unknown',
                        'confidence': decision_result.confidence if decision_result else 0.0,
                        'reasoning': decision_result.reasoning if decision_result else ''
                    }
                }), 400
            
            # 根據決策結果調整搜索參數
            if decision_result and decision_result.strategy != ProcessingStrategy.REJECT_QUERY:
                # 使用決策引擎推薦的平台
                if decision_result.recommended_platforms:
                    # 將平台名稱映射到Site枚舉
                    platform_mapping = {
                        'indeed': 'indeed',
                        'linkedin': 'linkedin', 
                        'seek': 'seek',
                        '104': '104',
                        'ziprecruiter': 'zip_recruiter'
                    }
                    
                    recommended_sites = []
                    for platform in decision_result.recommended_platforms:
                        if platform in platform_mapping:
                            recommended_sites.append(platform_mapping[platform])
                    
                    if recommended_sites and not selected_sites:
                        selected_sites = recommended_sites
                
                # 使用決策結果中的搜索參數
                if 'max_results' in decision_result.search_parameters:
                    results_wanted = min(decision_result.search_parameters['max_results'], results_wanted)
            
            # 如果LLM成功分析出結構化意圖，使用LLM的搜索條件
            if llm_intent_result.llm_used and llm_intent_result.structured_intent:
                structured_intent = llm_intent_result.structured_intent
                
                # 使用LLM提取的搜索條件覆蓋原始解析結果
                if structured_intent.job_titles:
                    # 將職位標題組合為搜索詞
                    parsed.search_term = ' OR '.join(structured_intent.job_titles)
                
                if structured_intent.location and not location:
                    # 如果LLM識別出地點且用戶未明確指定地點，使用LLM的地點
                    derived_location = structured_intent.location
                
                print(f"LLM意圖分析成功: 職位={structured_intent.job_titles}, 技能={structured_intent.skills}, 地點={structured_intent.location}")
                print(f"決策結果: 策略={decision_result.strategy.value if decision_result else 'unknown'}, 推薦平台={decision_result.recommended_platforms if decision_result else []}")
            else:
                print(f"使用基礎意圖分析: {parsed.search_term}")
                
        except Exception as e:
            print(f"智能意圖分析失敗: {e}")
            llm_intent_result = None
            decision_result = None
        
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
        print(f"開始搜尋: {parsed.search_term}")
        if site_name:
            print(f"指定搜尋網站: {site_name}")
        else:
            print(f"選擇的網站: {selected_sites if selected_sites else '所有網站'}")
            
        # 使用新的智能路由器
        if site_name:
            # 單平台搜尋
            result = smart_router.search_jobs(
                query=parsed.search_term,
                location=derived_location if derived_location else None,
                max_results=results_wanted,
                platforms=[site_name]
            )
        else:
            # 多平台智能搜尋
            result = smart_router.search_jobs(
                query=parsed.search_term,
                location=derived_location if derived_location else None,
                max_results=results_wanted
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
                    'successful_platforms': result.successful_platforms,
                    'failed_platforms': result.failed_platforms,
                    'execution_time': result.total_execution_time
                },
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            })
        
        # 轉換職位數據為字典格式
        jobs_list = []
        if result.jobs:
            for job in result.jobs:
                job_dict = {
                    'title': str(job.title or ''),
                    'company': str(job.company_name or ''),
                    'location': str(job.location.city if job.location else ''),
                    'description': str(job.description or '')[:500] + ('...' if len(str(job.description or '')) > 500 else ''),
                    'salary_min': None,  # 新架構中需要從compensation解析
                    'salary_max': None,  # 新架構中需要從compensation解析
                    'salary_currency': '',  # 新架構中需要從compensation解析
                    'date_posted': str(job.date_posted or ''),
                    'job_url': str(job.job_url or ''),
                    'job_url_direct': str(job.job_url_direct or ''),
                    'site': str(job.site or ''),
                    'job_type': str(job.job_type or ''),
                    'is_remote': bool(job.is_remote or False)
                }
                jobs_list.append(job_dict)

        # 可選：嚴格國家過濾（避免「澳洲」出現其他國家）
        strict_filter = os.environ.get('STRICT_COUNTRY_FILTER', 'false').lower() == 'true'
        if strict_filter and (derived_country or derived_location):
            country_tokens = set()
            if derived_country:
                country_tokens.add(derived_country.lower())
            # 常見同義詞
            synonyms = {
                'australia': ['australia', '澳洲', '澳大利亞', '澳大利亚'],
                'taiwan': ['taiwan', '台灣', '臺灣'],
                'hong kong': ['hong kong', '香港'],
                'singapore': ['singapore', '新加坡'],
                'japan': ['japan', '日本'],
                'usa': ['usa', 'united states', 'america', '美國', '美国'],
                'uk': ['uk', 'united kingdom', 'england', '英國', '英国'],
                'new zealand': ['new zealand', '紐西蘭', '新西蘭'],
                'canada': ['canada', '加拿大']
            }
            if derived_country and derived_country.lower() in synonyms:
                country_tokens.update(synonyms[derived_country.lower()])
            # 粗略過濾
            jobs_list = [j for j in jobs_list if any(tok in (j.get('location','').lower()) for tok in country_tokens)]

        # 快取搜尋結果
        search_results_cache[search_id] = {
            'result': result,
            'timestamp': datetime.now(),
            'query': parsed.search_term,
            'location': derived_location
        }
        
        # 伺服器端分頁切片
        total = len(jobs_list)
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        start = (page - 1) * per_page
        end = start + per_page
        page_jobs = jobs_list[start:end]
        
        # 返回成功響應（含分頁資訊）
        return jsonify({
            'success': True,
            'search_id': search_id,
            'total_jobs': total,
            'jobs': page_jobs,
            'routing_info': {
                'successful_platforms': result.successful_platforms,
                'failed_platforms': result.failed_platforms,
                'execution_time': result.total_execution_time,
                'search_metadata': result.search_metadata
            },
            'search_params': {
                'query': user_query,
                'location': location,
                'results_wanted': results_wanted,
                'hours_old': hours_old
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
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
    # 禁止快取，確保顯示最新資料
    resp = make_response(render_template('demo_results.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp


# ============ Auth Pages ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('登入成功', 'success')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        flash('帳號或密碼錯誤', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not email or not password:
            flash('請輸入完整資料', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('此 Email 已被註冊', 'error')
            return render_template('register.html')
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('註冊成功，已自動登入', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已登出', 'info')
    return redirect(url_for('index'))


@app.route('/favorites')
@login_required
def favorites_page():
    favs = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.saved_at.desc()).all()
    return render_template('favorites.html', favorites=favs)


# ============ Admin: Synthetic Test Runner ============

def run_synthetic_tests() -> int:
    """Run a suite of lightweight synthetic tests via Flask test_client.
    Returns run_id.
    """
    run = TestRun()
    db.session.add(run)
    db.session.commit()

    def record(name: str, status: str, start_t: float, message: str = ""):
        case = TestCaseResult(
            run_id=run.id,
            name=name,
            status=status,
            duration_ms=int((time.time() - start_t) * 1000),
            message=message[:2000]
        )
        db.session.add(case)
        db.session.commit()

    total = passed = failed = skipped = 0

    with app.test_client() as client:
        # Health
        total += 1
        t0 = time.time()
        try:
            r = client.get('/health')
            if r.status_code == 200 and r.json.get('status') == 'healthy':
                passed += 1; record('health', 'pass', t0)
            else:
                failed += 1; record('health', 'fail', t0, f"status={r.status_code}")
        except Exception as e:
            failed += 1; record('health', 'fail', t0, str(e))

        # Homepage
        total += 1
        t0 = time.time()
        try:
            r = client.get('/')
            if r.status_code == 200 and '智能職位搜尋'.encode('utf-8') in r.data:
                passed += 1; record('homepage', 'pass', t0)
            else:
                failed += 1; record('homepage', 'fail', t0, f"status={r.status_code}")
        except Exception as e:
            failed += 1; record('homepage', 'fail', t0, str(e))

        # Search (may return zero jobs; still pass if success flag)
        total += 1
        t0 = time.time()
        try:
            payload = {"query": "台北 AI 工程師", "results_wanted": 5, "hours_old": 168, "page": 1, "per_page": 5}
            r = client.post('/search', json=payload)
            if r.status_code == 200 and r.json.get('success'):
                passed += 1; record('search_basic', 'pass', t0, f"jobs={len(r.json.get('jobs', []))}")
                search_id = r.json.get('search_id')
                # Download JSON if jobs present
                if search_id and r.json.get('total_jobs', 0) > 0:
                    total += 1
                    t1 = time.time()
                    r2 = client.get(f"/download/{search_id}/json")
                    if r2.status_code == 200 and r2.mimetype == 'application/json':
                        passed += 1; record('download_json', 'pass', t1)
                    else:
                        failed += 1; record('download_json', 'fail', t1, f"status={r2.status_code}")
                else:
                    # Skip download if no results
                    total += 1; skipped += 1; record('download_json', 'skip', t0, 'no results')
            else:
                failed += 1; record('search_basic', 'fail', t0, f"status={r.status_code}")
        except Exception as e:
            failed += 1; record('search_basic', 'fail', t0, str(e))

        # Auth flow + favorites
        total += 1
        t0 = time.time()
        try:
            email = f"test+{int(time.time())}@example.com"
            r = client.post('/register', data={'email': email, 'password': 'P@ssw0rd!'}, follow_redirects=True)
            if r.status_code == 200:
                fav_payload = {
                    'title': 'Synthetic Tester', 'company': 'JobSeeker', 'location': '台北',
                    'site': 'linkedin', 'job_url': 'https://example.com', 'job_url_direct': ''
                }
                r2 = client.post('/api/favorites', json=fav_payload)
                if r2.status_code == 200 and r2.json.get('success'):
                    passed += 1; record('auth_favorite', 'pass', t0)
                else:
                    failed += 1; record('auth_favorite', 'fail', t0, f"status={r2.status_code}")
            else:
                failed += 1; record('auth_favorite', 'fail', t0, f"status={r.status_code}")
        except Exception as e:
            failed += 1; record('auth_favorite', 'fail', t0, str(e))

    run.total = total
    run.passed = passed
    run.failed = failed
    run.skipped = skipped
    run.finished_at = datetime.utcnow()
    run.duration_sec = (run.finished_at - run.started_at).total_seconds()
    db.session.commit()
    return run.id


@app.route('/admin/tests')
@login_required
@admin_required
def admin_tests_page():
    runs = TestRun.query.order_by(TestRun.id.desc()).limit(10).all()
    return render_template('admin_tests.html', runs=runs)


@app.route('/api/admin/run-tests', methods=['POST'])
@login_required
@admin_required
def api_admin_run_tests():
    run_id = run_synthetic_tests()
    return jsonify({'success': True, 'run_id': run_id})
@app.route('/api/favorites', methods=['GET', 'POST'])
@login_required
def favorites_api():
    if request.method == 'POST':
        data = request.get_json(force=True)
        fav = Favorite(
            user_id=current_user.id,
            title=data.get('title'),
            company=data.get('company'),
            location=data.get('location'),
            site=data.get('site'),
            job_url=data.get('job_url'),
            job_url_direct=data.get('job_url_direct')
        )
        db.session.add(fav)
        db.session.commit()
        return jsonify({'success': True, 'id': fav.id})
    # GET
    favs = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.saved_at.desc()).all()
    return jsonify({'success': True, 'favorites': [
        {
            'id': f.id,
            'title': f.title,
            'company': f.company,
            'location': f.location,
            'site': f.site,
            'job_url': f.job_url,
            'job_url_direct': f.job_url_direct,
            'saved_at': f.saved_at.isoformat()
        } for f in favs
    ]})


@app.route('/api/favorites/<int:fav_id>', methods=['DELETE'])
@login_required
def delete_favorite(fav_id):
    fav = Favorite.query.filter_by(id=fav_id, user_id=current_user.id).first()
    if not fav:
        return jsonify({'success': False, 'error': '找不到收藏'}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({'success': True})


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


@app.route('/api/search/<search_id>')
def get_search_result(search_id: str):
    """
    取得指定搜尋 ID 的結果（用於 Demo/結果頁動態顯示）
    """
    try:
        if search_id not in search_results_cache:
            return jsonify({'success': False, 'error': '搜尋結果不存在或已過期'}), 404

        cached = search_results_cache[search_id]
        result = cached['result']

        # 可選分頁參數
        try:
            page = int(request.args.get('page', 0))
        except Exception:
            page = 0
        try:
            per_page = int(request.args.get('per_page', 0))
        except Exception:
            per_page = 0

        jobs_list = []
        if result.combined_jobs_data is not None:
            df_clean = result.combined_jobs_data.fillna('')
            for _, row in df_clean.iterrows():
                jobs_list.append({
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
                })

        # 分頁切片（若提供 page/per_page）
        total = len(jobs_list)
        if page and per_page:
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 10
            total_pages = (total + per_page - 1) // per_page
            start = (page - 1) * per_page
            end = start + per_page
            page_jobs = jobs_list[start:end]
        else:
            total_pages = 1
            page_jobs = jobs_list
            page = 1
            per_page = total or 1

        return jsonify({
            'success': True,
            'search_id': search_id,
            'timestamp': cached['timestamp'].isoformat(),
            'query': cached.get('query'),
            'location': cached.get('location'),
            'total_jobs': result.total_jobs,
            'routing_info': {
                'successful_agents': [agent.value for agent in result.successful_agents],
                'failed_agents': [agent.value for agent in result.failed_agents],
                'confidence_score': result.routing_decision.confidence_score,
                'execution_time': result.total_execution_time
            },
            'jobs': page_jobs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search/latest')
def get_latest_search_result():
    """
    取得最近一次搜尋結果摘要
    """
    try:
        if not search_results_cache:
            return jsonify({'success': False, 'error': '尚無搜尋記錄'}), 404

        # 找出最新的搜尋
        latest_id = max(search_results_cache.items(), key=lambda kv: kv[1]['timestamp'])[0]
        return get_search_result(latest_id)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
        'zip_recruiter': '美國知名求職網站，AI 智能匹配',
        'google': 'Google 職位搜尋，整合多個平台',
        'naukri': '印度最大的求職網站',
        'bayt': '中東地區領先的求職平台',
        'bdjobs': '孟加拉國本地求職網站',
        '104': '台灣 104 人力銀行，本地在地平台',
        '1111': '台灣 1111 人力銀行，本地在地平台'
    }
    
    return descriptions.get(site.value, f'{site.value.title()} 求職網站')


@app.route('/docs')
def docs_page():
    """
    文檔頁面
    顯示 jobseeker 的使用文檔和 API 說明
    """
    return render_template('docs.html')


@app.route('/downloads')
def downloads_page():
    """
    下載頁面
    提供各種工具和資源的下載
    """
    return render_template('downloads.html')


@app.route('/donate')
def donate_page():
    """
    捐贈頁面
    支持專案發展的捐贈資訊
    """
    return render_template('donate.html')


@app.route('/search-results')
def search_results():
    """
    展示搜尋結果頁面 - 只顯示用戶搜尋結果
    """
    # 禁止快取，確保顯示最新資料
    resp = make_response(render_template('search_results.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp


# 註冊增強版 API Blueprint
try:
    from .enhanced_api import enhanced_api_bp
    app.register_blueprint(enhanced_api_bp)
    print("✅ 增強版 API (v2) 已註冊")
except ImportError as e:
    print(f"⚠️ 無法註冊增強版 API: {e}")

if __name__ == '__main__':
    # 從環境變數獲取主機地址，預設為 0.0.0.0 以支援外部訪問
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 jobseeker 網頁應用啟動中...")
    print(f"📱 本地訪問: http://localhost:{port}")
    print(f"📱 網路訪問: http://192.168.1.181:{port}")
    print(f"📊 API 文檔: http://localhost:{port}/api/sites")
    print(f"🔧 監聽地址: {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG']
    )
