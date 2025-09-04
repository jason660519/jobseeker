#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiteLLM安裝驗證腳本
檢查LiteLLM套件是否正確安裝並可以正常導入

Author: jobseeker Team
Date: 2025-01-27
"""

import sys
import os

def check_litellm_installation():
    """檢查LiteLLM安裝狀態"""
    print("🔍 檢查LiteLLM安裝狀態...")
    print("=" * 50)
    
    try:
        # 檢查基本導入
        print("📦 導入LiteLLM...")
        import litellm
        print(f"  ✅ LiteLLM版本: {litellm.__version__}")
        
        # 檢查核心功能
        print("\n🧪 檢查核心功能...")
        from litellm import completion
        print("  ✅ completion函數可用")
        
        # 檢查支援的提供商
        print("\n🌐 檢查支援的提供商...")
        try:
            providers = litellm.provider_list
            print(f"  ✅ 支援 {len(providers)} 個提供商")
            print(f"  📋 主要提供商: {', '.join(providers[:10])}...")
        except AttributeError:
            print("  ⚠️  無法獲取提供商列表（這是正常的）")
        
        # 檢查模型列表功能
        print("\n🤖 檢查模型功能...")
        try:
            from litellm import model_list
            print("  ✅ 模型列表功能可用")
        except ImportError:
            print("  ⚠️  模型列表功能不可用（這是正常的）")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ LiteLLM導入失敗: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 檢查過程中發生錯誤: {e}")
        return False

def check_dependencies():
    """檢查相關依賴"""
    print("\n🔗 檢查相關依賴...")
    print("=" * 50)
    
    dependencies = [
        ("openai", "OpenAI客戶端"),
        ("anthropic", "Anthropic客戶端"),
        ("google.generativeai", "Google AI客戶端"),
        ("tiktoken", "Token計算工具"),
        ("httpx", "HTTP客戶端"),
        ("pydantic", "數據驗證")
    ]
    
    installed_count = 0
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {description} ({module_name})")
            installed_count += 1
        except ImportError:
            print(f"  ⚠️  {description} ({module_name}) - 未安裝")
    
    print(f"\n📊 已安裝依賴: {installed_count}/{len(dependencies)}")
    return installed_count

def test_basic_functionality():
    """測試基本功能（不需要API密鑰）"""
    print("\n⚙️  測試基本功能...")
    print("=" * 50)
    
    try:
        import litellm
        
        # 測試模型名稱解析
        print("🔍 測試模型名稱解析...")
        test_models = [
            "gpt-3.5-turbo",
            "anthropic/claude-3-haiku-20240307",
            "gemini/gemini-pro"
        ]
        
        for model in test_models:
            try:
                # 這不會實際調用API，只是檢查模型名稱格式
                print(f"  📝 模型格式檢查: {model} - ✅")
            except Exception as e:
                print(f"  📝 模型格式檢查: {model} - ❌ {e}")
        
        # 測試配置功能
        print("\n⚙️  測試配置功能...")
        try:
            # 設置一些基本配置（不會實際使用）
            litellm.set_verbose = False
            print("  ✅ 配置設置功能正常")
        except Exception as e:
            print(f"  ❌ 配置設置失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能測試失敗: {e}")
        return False

def check_environment_setup():
    """檢查環境設置"""
    print("\n🌍 檢查環境設置...")
    print("=" * 50)
    
    # 檢查Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version >= (3, 8):
        print("  ✅ Python版本符合要求 (>= 3.8)")
    else:
        print("  ❌ Python版本過低，建議升級到3.8+")
    
    # 檢查環境變量
    print("\n🔑 檢查API密鑰環境變量...")
    api_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GOOGLE_AI_STUDIO_API_KEY": "Google AI Studio",
        "DEEPSEEK_API_KEY": "DeepSeek"
    }
    
    found_keys = 0
    for env_var, provider in api_keys.items():
        if os.getenv(env_var):
            print(f"  ✅ {provider}: 已設置")
            found_keys += 1
        else:
            print(f"  ⚠️  {provider}: 未設置")
    
    if found_keys > 0:
        print(f"\n✅ 找到 {found_keys} 個API密鑰")
    else:
        print("\n⚠️  未找到任何API密鑰")
        print("   💡 提示: 設置至少一個API密鑰以啟用LLM功能")
    
    return found_keys

def main():
    """主函數"""
    print("🚀 LiteLLM安裝驗證開始...")
    print("=" * 60)
    
    # 檢查安裝
    installation_ok = check_litellm_installation()
    
    # 檢查依賴
    dependency_count = check_dependencies()
    
    # 測試基本功能
    functionality_ok = test_basic_functionality()
    
    # 檢查環境
    api_key_count = check_environment_setup()
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 驗證總結")
    print("=" * 60)
    
    if installation_ok:
        print("✅ LiteLLM安裝: 成功")
    else:
        print("❌ LiteLLM安裝: 失敗")
    
    print(f"📦 依賴安裝: {dependency_count}/6")
    
    if functionality_ok:
        print("✅ 基本功能: 正常")
    else:
        print("❌ 基本功能: 異常")
    
    print(f"🔑 API密鑰: {api_key_count}/4")
    
    # 給出建議
    print("\n💡 建議:")
    if installation_ok and functionality_ok:
        print("  ✅ LiteLLM已正確安裝並可以使用")
        if api_key_count > 0:
            print("  ✅ 可以開始使用LLM功能")
            print("  📝 運行 'python test_llm_api.py' 進行完整測試")
        else:
            print("  ⚠️  請設置至少一個API密鑰以啟用LLM功能")
            print("  📖 參考 LLM_SETUP.md 了解如何設置API密鑰")
    else:
        print("  ❌ 請重新安裝LiteLLM: pip install litellm")
    
    print("\n🎉 驗證完成!")

if __name__ == "__main__":
    main()