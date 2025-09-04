#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試各家LLM對於用戶查詢的JSON回應格式
測試查詢："我要找澳洲 ai工程師的工作，請幫我找SYDNEY CITY 20KM 範圍內的"
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

from jobseeker.llm_config import LLMProvider, config_manager
from jobseeker.llm_client import create_llm_client

def test_llm_json_response(provider: LLMProvider, user_query: str) -> dict:
    """
    測試單個LLM提供商對用戶查詢的JSON回應
    
    Args:
        provider: LLM提供商
        user_query: 用戶查詢內容
        
    Returns:
        dict: 測試結果
    """
    result = {
        'provider': provider.value,
        'model': None,
        'success': False,
        'response_time': None,
        'json_response': None,
        'raw_response': None,
        'error_message': None,
        'json_valid': False
    }
    
    try:
        # 獲取配置
        config = config_manager.get_config(provider)
        
        if not config.is_valid():
            result['error_message'] = "配置無效或API密鑰未設置"
            return result
            
        result['model'] = config.model_name
        
        # 創建客戶端
        client = create_llm_client(config)
        
        # 構建英文標準化提示詞，要求返回JSON格式
        system_prompt = """
You are a professional job search assistant. Based on user query requirements, parse and return structured JSON format response.

Please respond strictly in the following JSON format:
{
  "search_intent": "job_search",
  "location": {
    "country": "Australia",
    "city": "Sydney",
    "radius_km": 20,
    "specific_area": "Sydney City"
  },
  "job_criteria": {
    "position": "AI Engineer",
    "keywords": ["AI", "artificial intelligence", "machine learning", "deep learning"],
    "industry": "technology"
  },
  "search_parameters": {
    "location_filter": "Sydney City 20km radius",
    "job_type": "full-time",
    "experience_level": "all"
  }
}

Return only JSON, do not add any other text explanations.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        # 發送請求
        start_time = time.time()
        response = client.call(
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
        end_time = time.time()
        
        result['response_time'] = round(end_time - start_time, 2)
        
        if response.success:
            result['success'] = True
            result['raw_response'] = response.content
            
            # 嘗試解析JSON
            try:
                # 清理回應內容，移除可能的markdown格式
                clean_content = response.content.strip()
                if clean_content.startswith('```json'):
                    clean_content = clean_content[7:]
                if clean_content.endswith('```'):
                    clean_content = clean_content[:-3]
                clean_content = clean_content.strip()
                
                parsed_json = json.loads(clean_content)
                result['json_response'] = parsed_json
                result['json_valid'] = True
                
            except json.JSONDecodeError as e:
                result['error_message'] = f"JSON解析失敗: {str(e)}"
                result['json_valid'] = False
                
        else:
            result['error_message'] = response.error_message
            
    except Exception as e:
        result['error_message'] = str(e)
        
    return result

def format_json_display(json_obj, indent=2):
    """
    格式化JSON顯示
    
    Args:
        json_obj: JSON對象
        indent: 縮進空格數
        
    Returns:
        str: 格式化的JSON字符串
    """
    if json_obj is None:
        return "無JSON回應"
    
    try:
        return json.dumps(json_obj, ensure_ascii=False, indent=indent)
    except Exception:
        return str(json_obj)

def main():
    """
    主測試函數
    """
    user_query = "我要找澳洲 ai工程師的工作，請幫我找SYDNEY CITY 20KM 範圍內的"
    
    print("🧪 測試各家LLM對用戶查詢的JSON回應格式")
    print("=" * 80)
    print(f"📝 測試查詢: {user_query}")
    print("=" * 80)
    
    # 定義要測試的雲端LLM提供商
    cloud_providers = [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.GOOGLE,
        LLMProvider.DEEPSEEKER,
        LLMProvider.OPENROUTER
    ]
    
    results = []
    successful_responses = 0
    valid_json_count = 0
    
    for provider in cloud_providers:
        print(f"\n🔍 測試 {provider.value.upper()}...")
        
        result = test_llm_json_response(provider, user_query)
        results.append(result)
        
        if result['success']:
            successful_responses += 1
            print(f"✅ 回應成功 (模型: {result['model']}, 時間: {result['response_time']}秒)")
            
            if result['json_valid']:
                valid_json_count += 1
                print("✅ JSON格式有效")
                print("📋 JSON回應內容:")
                print(format_json_display(result['json_response']))
            else:
                print("❌ JSON格式無效")
                print(f"🚫 錯誤: {result['error_message']}")
                print("📄 原始回應:")
                print(result['raw_response'][:500] + "..." if len(result['raw_response']) > 500 else result['raw_response'])
        else:
            print(f"❌ 回應失敗: {result['error_message']}")
    
    # 總結報告
    print("\n" + "=" * 80)
    print("📊 **測試結果總結**")
    print(f"🔢 總共測試: {len(cloud_providers)} 個LLM提供商")
    print(f"✅ 成功回應: {successful_responses} 個")
    print(f"📋 有效JSON: {valid_json_count} 個")
    print(f"📈 成功率: {(successful_responses/len(cloud_providers)*100):.1f}%")
    print(f"📈 JSON有效率: {(valid_json_count/len(cloud_providers)*100):.1f}%")
    
    # 詳細比較
    print("\n📋 **各家LLM JSON回應比較:**")
    for result in results:
        print(f"\n🏷️ **{result['provider'].upper()}**")
        if result['success'] and result['json_valid']:
            print(f"   ✅ 狀態: 成功 (模型: {result['model']})")
            print(f"   ⏱️ 響應時間: {result['response_time']}秒")
            print("   📋 JSON結構:")
            
            # 分析JSON結構
            json_obj = result['json_response']
            if isinstance(json_obj, dict):
                for key, value in json_obj.items():
                    if isinstance(value, dict):
                        print(f"      • {key}: {{...}} (包含 {len(value)} 個字段)")
                    elif isinstance(value, list):
                        print(f"      • {key}: [...] (包含 {len(value)} 個項目)")
                    else:
                        print(f"      • {key}: {type(value).__name__}")
        else:
            status = "配置問題" if "配置無效" in str(result['error_message']) else "回應失敗"
            print(f"   ❌ 狀態: {status}")
            if result['error_message']:
                print(f"   🚫 原因: {result['error_message']}")
    
    # 最佳實踐建議
    if valid_json_count > 0:
        print("\n💡 **最佳實踐建議:**")
        print("   • 所有成功的LLM都能理解中文查詢並返回結構化JSON")
        print("   • 建議在系統提示詞中明確指定JSON格式要求")
        print("   • 可以根據不同LLM的回應特點調整解析邏輯")
        print("   • 建議實施JSON驗證和錯誤處理機制")
    
    return results

if __name__ == "__main__":
    results = main()