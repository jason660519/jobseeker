#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的LLM API測試
測試可用的LLM提供商並驗證意圖分析功能

Author: jobseeker Team
Date: 2025-01-27
"""

import os
import json
import time
from typing import Dict, Any

def test_openai_with_litellm():
    """使用LiteLLM測試OpenAI API"""
    print("🧪 測試OpenAI API (通過LiteLLM)...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("  ❌ OpenAI API密鑰未設置")
        return False
    
    try:
        import litellm
        
        # 設置API密鑰
        os.environ["OPENAI_API_KEY"] = api_key
        
        # 簡單的測試消息
        messages = [
            {"role": "system", "content": "你是一個求職意圖分析助手。請用JSON格式回應。"},
            {"role": "user", "content": "我想找Python工程師的工作"}
        ]
        
        print("  📤 發送API請求...")
        start_time = time.time()
        
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.1
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"  ✅ API調用成功 ({response_time:.2f}s)")
        print(f"  📝 響應內容: {response.choices[0].message.content[:100]}...")
        
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"  📊 Token使用: {usage.prompt_tokens} + {usage.completion_tokens} = {usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI測試失敗: {e}")
        return False

def test_anthropic_with_litellm():
    """使用LiteLLM測試Anthropic API"""
    print("\n🧪 測試Anthropic API (通過LiteLLM)...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ❌ Anthropic API密鑰未設置")
        return False
    
    try:
        import litellm
        
        # 設置API密鑰
        os.environ["ANTHROPIC_API_KEY"] = api_key
        
        # 簡單的測試消息
        messages = [
            {"role": "system", "content": "你是一個求職意圖分析助手。請用JSON格式回應。"},
            {"role": "user", "content": "台北的前端開發職位"}
        ]
        
        print("  📤 發送API請求...")
        start_time = time.time()
        
        # 使用正確的Anthropic模型名稱
        response = litellm.completion(
            model="anthropic/claude-3-haiku-20240307",
            messages=messages,
            max_tokens=200,
            temperature=0.1
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"  ✅ API調用成功 ({response_time:.2f}s)")
        print(f"  📝 響應內容: {response.choices[0].message.content[:100]}...")
        
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"  📊 Token使用: {usage.prompt_tokens} + {usage.completion_tokens} = {usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Anthropic測試失敗: {e}")
        return False

def test_intent_analysis():
    """測試意圖分析功能"""
    print("\n🧠 測試意圖分析功能...")
    
    # 選擇可用的提供商
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("  ❌ 沒有可用的API密鑰")
        return False
    
    try:
        import litellm
        
        # 選擇模型
        if openai_key:
            model = "gpt-3.5-turbo"
            print("  🤖 使用OpenAI模型")
        else:
            model = "anthropic/claude-3-haiku-20240307"
            print("  🤖 使用Anthropic模型")
        
        # 意圖分析提示
        system_prompt = """
你是一個專業的求職意圖分析AI助手。請分析用戶查詢並以JSON格式回應：

{
  "is_job_related": boolean,
  "intent_type": "job_search" | "career_advice" | "non_job_related",
  "confidence": float (0.0-1.0),
  "reasoning": "分析原因",
  "structured_intent": {
    "job_titles": ["職位名稱"],
    "skills": ["技能關鍵詞"],
    "locations": ["地點"]
  }
}
"""
        
        test_queries = [
            "我想找AI工程師的工作",
            "今天天氣如何？"
        ]
        
        for query in test_queries:
            print(f"\n  📝 測試查詢: {query}")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"請分析這個查詢: {query}"}
            ]
            
            try:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    max_tokens=300,
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                print(f"    📤 響應: {content[:150]}...")
                
                # 嘗試解析JSON
                try:
                    analysis = json.loads(content)
                    is_job_related = analysis.get('is_job_related', False)
                    confidence = analysis.get('confidence', 0.0)
                    print(f"    ✅ 求職相關: {is_job_related}, 置信度: {confidence}")
                except json.JSONDecodeError:
                    print("    ⚠️  響應不是有效的JSON格式")
                
            except Exception as e:
                print(f"    ❌ 查詢失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 意圖分析測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 簡單LLM API測試開始...")
    print("=" * 50)
    
    # 檢查LiteLLM導入
    try:
        import litellm
        print("✅ LiteLLM導入成功")
    except ImportError:
        print("❌ LiteLLM導入失敗，請安裝: pip install litellm")
        return
    
    # 測試結果
    results = []
    
    # 測試OpenAI
    if os.getenv("OPENAI_API_KEY"):
        results.append(("OpenAI", test_openai_with_litellm()))
    else:
        print("⚠️  跳過OpenAI測試 - API密鑰未設置")
    
    # 測試Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        results.append(("Anthropic", test_anthropic_with_litellm()))
    else:
        print("⚠️  跳過Anthropic測試 - API密鑰未設置")
    
    # 測試意圖分析
    if any(result[1] for result in results):
        results.append(("意圖分析", test_intent_analysis()))
    
    # 總結
    print("\n" + "=" * 50)
    print("📋 測試總結")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if success:
            success_count += 1
    
    if success_count > 0:
        print(f"\n🎉 {success_count}/{len(results)} 項測試成功!")
        print("💡 LiteLLM已正確安裝並可以使用")
        print("📝 您可以在應用程序中使用LLM功能")
    else:
        print("\n❌ 所有測試失敗")
        print("💡 請檢查API密鑰設置和網絡連接")

if __name__ == "__main__":
    main()