#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenRouter API 測試腳本
用於驗證 OpenRouter API 密鑰是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from jobseeker.llm_config import LLMProvider, get_current_llm_config, set_llm_provider
from jobseeker.llm_client import create_llm_client

def test_openrouter_api():
    """
    測試 OpenRouter API 連接和功能
    """
    print("🧪 開始測試 OpenRouter API...")
    
    try:
        # 設置使用 OpenRouter 提供商
        print("📝 設置 LLM 提供商為 OpenRouter...")
        success = set_llm_provider(LLMProvider.OPENROUTER)
        if not success:
            print("❌ 無法設置 OpenRouter 提供商")
            return False
            
        # 獲取當前配置
        config = get_current_llm_config()
        print(f"✅ 當前配置: {config.provider.value}")
        print(f"🔑 API 密鑰: {'已設置' if config.api_key else '未設置'}")
        print(f"🤖 模型: {config.model_name}")
        
        if not config.api_key:
            print("❌ OpenRouter API 密鑰未設置")
            return False
            
        # 創建 LLM 客戶端
        print("🔧 創建 LLM 客戶端...")
        client = create_llm_client(config)
        
        # 測試簡單的 LLM 調用
        print("💬 測試 LLM 調用...")
        test_prompt = "Please answer in one sentence: What is artificial intelligence?"
        
        response = client.call(test_prompt)
        
        if response and response.content:
            print(f"✅ LLM 回應成功!")
            print(f"📝 回應內容: {response.content[:100]}...")
            print(f"🏷️ 模型: {response.model}")
            print(f"⏱️ 處理時間: {response.processing_time:.2f}秒")
            return True
        else:
            print("❌ LLM 回應為空")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_intent_analysis():
    """
    測試意圖分析功能
    """
    print("\n🎯 測試意圖分析功能...")
    
    try:
        from jobseeker.intent_analyzer import IntentAnalyzer
        
        # 創建意圖分析器
        analyzer = IntentAnalyzer()
        
        # 測試求職相關查詢
        test_queries = [
            "我想找台北的Python工程師工作",
            "尋找薪資50k以上的前端開發職位",
            "今天天氣如何？"  # 非求職查詢
        ]
        
        for query in test_queries:
            print(f"\n📝 測試查詢: {query}")
            result = analyzer.analyze_intent(query)
            
            print(f"✅ 分析結果:")
            print(f"   - 是否求職相關: {result.is_job_related}")
            print(f"   - 意圖類型: {result.intent_type.value}")
            print(f"   - 關鍵詞: {result.keywords_matched}")
            print(f"   - 置信度: {result.confidence:.2f}")
            
        return True
        
    except Exception as e:
        print(f"❌ 意圖分析測試失敗: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 OpenRouter API 測試開始")
    print("=" * 50)
    
    # 測試基本 API 功能
    api_test_success = test_openrouter_api()
    
    # 測試意圖分析功能
    intent_test_success = test_intent_analysis()
    
    print("\n" + "=" * 50)
    print("📊 測試結果摘要:")
    print(f"   - OpenRouter API: {'✅ 通過' if api_test_success else '❌ 失敗'}")
    print(f"   - 意圖分析: {'✅ 通過' if intent_test_success else '❌ 失敗'}")
    
    if api_test_success and intent_test_success:
        print("\n🎉 所有測試通過！OpenRouter API 配置成功！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")
        sys.exit(1)