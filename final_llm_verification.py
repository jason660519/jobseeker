#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終LLM驗證腳本
用於確認LiteLLM套件安裝狀態和可用的LLM API
"""

import os
import sys
from typing import Dict, List, Tuple

def check_litellm_installation() -> Tuple[bool, str]:
    """
    檢查LiteLLM套件安裝狀態
    
    Returns:
        Tuple[bool, str]: (是否安裝成功, 詳細信息)
    """
    try:
        import litellm
        # 嘗試獲取版本信息
        try:
            version = getattr(litellm, '__version__', 'Unknown')
        except:
            version = 'Unknown'
        
        # 檢查核心功能
        has_completion = hasattr(litellm, 'completion')
        has_acompletion = hasattr(litellm, 'acompletion')
        
        return True, f"LiteLLM已安裝 (版本: {version}), 核心功能可用: completion={has_completion}, acompletion={has_acompletion}"
    except ImportError as e:
        return False, f"LiteLLM未安裝: {e}"
    except Exception as e:
        return False, f"LiteLLM檢查失敗: {e}"

def check_api_keys() -> Dict[str, bool]:
    """
    檢查各種LLM API密鑰的可用性
    
    Returns:
        Dict[str, bool]: API密鑰可用性字典
    """
    api_keys = {
        'OpenAI': bool(os.getenv('OPENAI_API_KEY')),
        'Anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
        'Google AI Studio': bool(os.getenv('GOOGLE_API_KEY')),
        'DeepSeek': bool(os.getenv('DEEPSEEK_API_KEY'))
    }
    return api_keys

def test_working_apis() -> List[str]:
    """
    測試可用的LLM API
    
    Returns:
        List[str]: 可用的API提供商列表
    """
    working_apis = []
    
    try:
        import litellm
        
        # 測試Anthropic API
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                response = litellm.completion(
                    model="anthropic/claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                if response and response.choices:
                    working_apis.append('Anthropic')
            except Exception as e:
                print(f"Anthropic API測試失敗: {e}")
        
        # 測試OpenAI API
        if os.getenv('OPENAI_API_KEY'):
            try:
                response = litellm.completion(
                    model="openai/gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                if response and response.choices:
                    working_apis.append('OpenAI')
            except Exception as e:
                print(f"OpenAI API測試失敗: {e}")
        
        # 測試Google API
        if os.getenv('GOOGLE_API_KEY'):
            try:
                response = litellm.completion(
                    model="google/gemini-pro",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                if response and response.choices:
                    working_apis.append('Google')
            except Exception as e:
                print(f"Google API測試失敗: {e}")
        
        # 測試DeepSeek API
        if os.getenv('DEEPSEEK_API_KEY'):
            try:
                response = litellm.completion(
                    model="deepseek/deepseek-chat",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                if response and response.choices:
                    working_apis.append('DeepSeek')
            except Exception as e:
                print(f"DeepSeek API測試失敗: {e}")
                
    except ImportError:
        print("LiteLLM未安裝，無法測試API")
    except Exception as e:
        print(f"API測試過程中發生錯誤: {e}")
    
    return working_apis

def main():
    """
    主函數：執行完整的LLM驗證流程
    """
    print("=" * 60)
    print("🔍 LiteLLM套件與API驗證報告")
    print("=" * 60)
    
    # 1. 檢查LiteLLM安裝狀態
    print("\n📦 1. LiteLLM套件安裝檢查")
    print("-" * 40)
    is_installed, install_info = check_litellm_installation()
    if is_installed:
        print(f"✅ {install_info}")
    else:
        print(f"❌ {install_info}")
        print("💡 建議執行: pip install litellm")
        return
    
    # 2. 檢查API密鑰
    print("\n🔑 2. API密鑰可用性檢查")
    print("-" * 40)
    api_keys = check_api_keys()
    available_keys = []
    for provider, available in api_keys.items():
        status = "✅" if available else "❌"
        print(f"{status} {provider}: {'已設置' if available else '未設置'}")
        if available:
            available_keys.append(provider)
    
    if not available_keys:
        print("\n⚠️  警告: 未檢測到任何API密鑰")
        print("💡 請設置至少一個API密鑰以使用LLM功能")
        return
    
    # 3. 測試可用的API
    print("\n🧪 3. API功能測試")
    print("-" * 40)
    working_apis = test_working_apis()
    
    if working_apis:
        print(f"✅ 可用的API提供商: {', '.join(working_apis)}")
    else:
        print("❌ 沒有可用的API提供商")
    
    # 4. 總結報告
    print("\n📊 4. 總結報告")
    print("=" * 60)
    print(f"LiteLLM套件: {'✅ 已安裝' if is_installed else '❌ 未安裝'}")
    print(f"可用API密鑰: {len(available_keys)}/4")
    print(f"可用API提供商: {len(working_apis)}/4")
    
    if working_apis:
        print(f"\n🎉 推薦使用: {working_apis[0]}")
        print("\n✅ LLM功能已準備就緒，可以進行用戶意圖分析！")
    else:
        print("\n⚠️  LLM功能不可用，建議檢查API密鑰設置")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()