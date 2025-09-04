#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM API測試腳本
測試LiteLLM客戶端和不同LLM提供商的可用性

Author: jobseeker Team
Date: 2025-01-27
"""

import os
import json
import sys
from typing import Dict, Any

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_config import LLMProvider, LLMConfig
from jobseeker.litellm_client import create_litellm_client, test_multiple_providers


def test_intent_analysis_with_llm(provider: LLMProvider, api_key: str) -> Dict[str, Any]:
    """測試意圖分析功能"""
    print(f"\n🧪 測試 {provider.value} 的意圖分析功能...")
    
    try:
        # 創建配置
        config = LLMConfig(
            provider=provider,
            api_key=api_key,
            temperature=0.1,
            max_tokens=1000
        )
        
        # 創建客戶端
        client = create_litellm_client(config)
        
        # 測試意圖分析
        test_queries = [
            "我想找AI工程師的工作",
            "台北的前端開發職位",
            "今天天氣如何？",
            "Python後端工程師 薪資50k以上"
        ]
        
        results = []
        
        for query in test_queries:
            print(f"  📝 測試查詢: {query}")
            
            # 構建意圖分析提示
            system_prompt = """
你是一個專業的求職意圖分析AI助手。請分析用戶查詢並以JSON格式回應：

{
  "is_job_related": boolean,
  "intent_type": "job_search" | "career_advice" | "non_job_related" | "unclear",
  "confidence": float (0.0-1.0),
  "reasoning": "分析原因",
  "structured_intent": {
    "job_titles": ["職位名稱"],
    "skills": ["技能關鍵詞"],
    "locations": ["地點"],
    "salary_range": "薪資範圍或null"
  },
  "search_suggestions": ["搜索建議"]
}
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"請分析這個查詢: {query}"}
            ]
            
            response = client.call(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if response.success:
                try:
                    analysis = json.loads(response.content)
                    results.append({
                        "query": query,
                        "analysis": analysis,
                        "response_time": response.response_time,
                        "usage": response.usage
                    })
                    print(f"    ✅ 分析成功 - 求職相關: {analysis.get('is_job_related')}")
                except json.JSONDecodeError as e:
                    print(f"    ❌ JSON解析失敗: {e}")
                    print(f"    原始響應: {response.content[:200]}...")
            else:
                print(f"    ❌ API調用失敗: {response.error_message}")
        
        return {
            "success": True,
            "provider": provider.value,
            "results": results
        }
        
    except Exception as e:
        print(f"    ❌ 測試失敗: {e}")
        return {
            "success": False,
            "provider": provider.value,
            "error": str(e)
        }


def test_basic_connection():
    """測試基本連接"""
    print("🔍 檢查環境變量中的API密鑰...")
    
    api_keys = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GOOGLE_AI_STUDIO_API_KEY"),
        "deepseeker": os.getenv("DEEPSEEK_API_KEY")
    }
    
    available_keys = {k: v for k, v in api_keys.items() if v}
    
    if not available_keys:
        print("⚠️  未找到任何API密鑰，請設置以下環境變量之一:")
        print("   - OPENAI_API_KEY")
        print("   - ANTHROPIC_API_KEY")
        print("   - GOOGLE_AI_STUDIO_API_KEY")
        print("   - DEEPSEEK_API_KEY")
        return False
    
    print(f"✅ 找到 {len(available_keys)} 個API密鑰: {list(available_keys.keys())}")
    
    # 測試連接
    print("\n🔗 測試LLM提供商連接...")
    results = test_multiple_providers(api_keys)
    
    for provider, result in results.items():
        if result["success"]:
            print(f"  ✅ {provider}: 連接成功 ({result.get('response_time', 0):.2f}s)")
        else:
            print(f"  ❌ {provider}: {result.get('error', '未知錯誤')}")
    
    return any(result["success"] for result in results.values())


def main():
    """主測試函數"""
    print("🚀 LLM API測試開始...")
    print("=" * 50)
    
    # 測試基本連接
    if not test_basic_connection():
        print("\n❌ 所有LLM提供商連接失敗，請檢查API密鑰設置")
        return
    
    # 測試意圖分析功能
    print("\n" + "=" * 50)
    print("🧠 測試意圖分析功能...")
    
    # 優先測試OpenAI（如果可用）
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        intent_result = test_intent_analysis_with_llm(LLMProvider.OPENAI, openai_key)
        
        if intent_result["success"]:
            print("\n📊 意圖分析測試結果:")
            for result in intent_result["results"]:
                query = result["query"]
                analysis = result["analysis"]
                print(f"\n  查詢: {query}")
                print(f"  求職相關: {analysis.get('is_job_related')}")
                print(f"  意圖類型: {analysis.get('intent_type')}")
                print(f"  置信度: {analysis.get('confidence')}")
                if analysis.get('structured_intent'):
                    structured = analysis['structured_intent']
                    if structured.get('job_titles'):
                        print(f"  職位: {structured['job_titles']}")
                    if structured.get('locations'):
                        print(f"  地點: {structured['locations']}")
    
    # 測試其他提供商
    other_providers = [
        (LLMProvider.ANTHROPIC, os.getenv("ANTHROPIC_API_KEY")),
        (LLMProvider.GOOGLE, os.getenv("GOOGLE_AI_STUDIO_API_KEY")),
        (LLMProvider.DEEPSEEKER, os.getenv("DEEPSEEK_API_KEY"))
    ]
    
    for provider, api_key in other_providers:
        if api_key:
            test_intent_analysis_with_llm(provider, api_key)
    
    print("\n" + "=" * 50)
    print("✅ LLM API測試完成")
    print("\n💡 如果測試成功，您可以在應用程序中使用相應的API密鑰")
    print("   設置環境變量後重啟應用程序即可啟用真實LLM功能")


if __name__ == "__main__":
    main()