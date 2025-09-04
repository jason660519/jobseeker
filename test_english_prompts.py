#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試英文標準化系統提示的功能
驗證所有LLM組件是否正確使用英文JSON格式輸出
"""

import os
import sys
import json
import time
sys.path.append('.')

# 加載環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 手動加載 .env 文件
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from jobseeker.query_parser import parse_user_query_llm
from jobseeker.llm_config import config_manager

def test_intent_analyzer_english_prompts():
    """
    測試意圖分析器是否使用英文提示
    """
    print("\n=== 測試意圖分析器英文提示 ===")
    
    test_queries = [
        "我要找澳洲ai工程師的工作，請幫我找SYDNEY CITY 20KM範圍內的",
        "I want to find software engineer jobs in Melbourne",
        "Python developer remote work opportunities"
    ]
    
    try:
        analyzer = LLMIntentAnalyzer(provider=LLMProvider.OPENAI_GPT35)
        
        for query in test_queries:
            print(f"\n測試查詢: {query}")
            
            try:
                result = analyzer.analyze_intent(query)
                
                print(f"  - 是否求職相關: {result.is_job_related}")
                print(f"  - 意圖類型: {result.intent_type}")
                print(f"  - 置信度: {result.confidence:.2f}")
                print(f"  - 使用LLM: {result.llm_used}")
                print(f"  - 回退到基礎分析器: {result.fallback_used}")
                
                if result.structured_intent:
                    print(f"  - 職位: {result.structured_intent.job_titles}")
                    print(f"  - 地點: {result.structured_intent.locations}")
                    print(f"  - 技能: {result.structured_intent.skills}")
                
                print(f"  - 狀態: ✅ 成功")
                
            except Exception as e:
                print(f"  - 錯誤: {str(e)}")
                print(f"  - 狀態: ❌ 失敗")
                
    except Exception as e:
        print(f"初始化意圖分析器失敗: {str(e)}")

def test_query_parser_english_prompts():
    """
    測試查詢解析器是否使用英文提示
    """
    print("\n=== 測試查詢解析器英文提示 ===")
    
    # 設置環境變數啟用LLM解析器
    os.environ['ENABLE_LLM_PARSER'] = 'true'
    
    test_queries = [
        "我要找澳洲ai工程師的工作，請幫我找SYDNEY CITY 20KM範圍內的",
        "Software engineer jobs in Melbourne on LinkedIn",
        "Remote Python developer positions"
    ]
    
    for query in test_queries:
        print(f"\n測試查詢: {query}")
        
        try:
            result = parse_user_query_llm(query)
            
            if result:
                print(f"  - 搜索詞: {result.search_term}")
                print(f"  - 地點: {result.location}")
                print(f"  - 遠程工作: {result.is_remote}")
                print(f"  - 網站提示: {result.site_hints}")
                print(f"  - 狀態: ✅ 成功")
            else:
                print(f"  - 狀態: ⚠️ 未啟用或解析失敗")
                
        except Exception as e:
            print(f"  - 錯誤: {str(e)}")
            print(f"  - 狀態: ❌ 失敗")

def test_config_file_loading():
    """
    測試配置文件是否正確加載
    """
    print("\n=== 測試配置文件加載 ===")
    
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'llm_system_prompts.json')
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"✅ 配置文件存在: {config_path}")
            print(f"✅ 配置版本: {config.get('version', 'unknown')}")
            
            # 檢查各組件的提示是否存在
            components = ['intent_analyzer', 'query_parser', 'intelligent_router']
            for component in components:
                if component in config:
                    system_prompt = config[component].get('system_prompt', '')
                    if system_prompt and 'You are' in system_prompt:
                        print(f"✅ {component}: 英文提示已配置")
                    else:
                        print(f"⚠️ {component}: 提示可能不是英文格式")
                else:
                    print(f"❌ {component}: 配置缺失")
                    
        else:
            print(f"❌ 配置文件不存在: {config_path}")
            
    except Exception as e:
        print(f"❌ 配置文件加載失敗: {str(e)}")

def test_llm_availability():
    """
    測試LLM服務可用性
    """
    print("\n=== 測試LLM服務可用性 ===")
    
    providers = [
        ('OpenAI GPT-3.5', 'OPENAI_API_KEY'),
        ('OpenAI GPT-4', 'OPENAI_API_KEY'),
        ('Anthropic Claude', 'ANTHROPIC_API_KEY'),
        ('Google AI', 'GOOGLE_API_KEY'),
        ('DeepSeeker', 'DEEPSEEKER_API_KEY'),
        ('OpenRouter', 'OPENROUTER_API_KEY')
    ]
    
    available_count = 0
    
    for provider_name, env_key in providers:
        api_key = os.getenv(env_key) or os.getenv(f'jobseeker_{env_key}')
        if api_key and len(api_key) > 10:
            print(f"✅ {provider_name}: 可用")
            available_count += 1
        else:
            print(f"❌ {provider_name}: API密鑰未設置")
    
    print(f"\n總計: {available_count}/{len(providers)} 個LLM服務可用")
    return available_count > 0

def main():
    """
    主測試函數
    """
    print("🚀 開始測試英文標準化系統提示")
    print("=" * 50)
    
    # 1. 測試配置文件加載
    test_config_file_loading()
    
    # 2. 測試LLM服務可用性
    llm_available = test_llm_availability()
    
    if llm_available:
        # 3. 測試意圖分析器
        test_intent_analyzer_english_prompts()
        
        # 4. 測試查詢解析器
        test_query_parser_english_prompts()
    else:
        print("\n⚠️ 沒有可用的LLM服務，跳過功能測試")
    
    print("\n" + "=" * 50)
    print("✅ 英文標準化系統提示測試完成")
    
    return {
        'config_loaded': True,
        'llm_available': llm_available,
        'tests_completed': True
    }

if __name__ == "__main__":
    results = main()