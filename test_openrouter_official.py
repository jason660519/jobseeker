#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenRouter API 官方測試腳本
根據 OpenRouter 官方文檔進行測試
"""

import os
import sys
sys.path.append('.')

# 加載 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 文件已加載")
except ImportError:
    print("⚠️ python-dotenv 未安裝，嘗試手動加載 .env")
    # 手動加載 .env 文件
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ .env 文件手動加載成功")
    except FileNotFoundError:
        print("❌ .env 文件未找到")
    except Exception as e:
        print(f"❌ 加載 .env 文件失敗: {e}")

from jobseeker.llm_config import LLMProvider, config_manager
from jobseeker.llm_client import create_llm_client

def test_openrouter_official():
    """
    根據 OpenRouter 官方文檔測試 API
    """
    print("🧪 開始測試 OpenRouter API（官方文檔版本）...")
    
    # 檢查 API 密鑰
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('jobseeker_OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OpenRouter API 密鑰未設置")
        return False
    
    print(f"✅ API 密鑰已設置: {api_key[:10]}...")
    
    try:
        # 獲取 OpenRouter 配置
        config = config_manager.get_config(LLMProvider.OPENROUTER)
        print(f"📝 配置信息:")
        print(f"   - 提供商: {config.provider.value}")
        print(f"   - 模型: {config.model_name}")
        print(f"   - 溫度: {config.temperature}")
        print(f"   - 最大令牌: {config.max_tokens}")
        
        # 創建客戶端
        print("🔧 創建 OpenRouter 客戶端...")
        client = create_llm_client(config)
        
        # 測試簡單的對話
        print("💬 測試簡單對話...")
        messages = [
            {"role": "user", "content": "Hello! Please respond with a simple greeting."}
        ]
        
        response = client.call(messages, temperature=0.1, max_tokens=50)
        
        if response.success:
            print("✅ OpenRouter API 調用成功！")
            print(f"📤 回應: {response.content}")
            print(f"🔧 模型: {response.model}")
            print(f"⏱️ 響應時間: {response.response_time:.2f}秒")
            print(f"📊 使用情況: {response.usage}")
            return True
        else:
            print(f"❌ OpenRouter API 調用失敗: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openrouter_models():
    """
    測試不同的 OpenRouter 模型
    """
    print("\n🎯 測試不同的 OpenRouter 模型...")
    
    # 測試模型列表
    test_models = [
        "openai/gpt-4o-mini",
        "openai/gpt-3.5-turbo",
        "anthropic/claude-3-haiku"
    ]
    
    for model in test_models:
        print(f"\n🧪 測試模型: {model}")
        
        try:
            # 創建臨時配置
            config = config_manager.get_config(LLMProvider.OPENROUTER)
            config.model_name = model
            
            client = create_llm_client(config)
            
            messages = [
                {"role": "user", "content": "Say 'Hello from " + model + "'"}
            ]
            
            response = client.call(messages, temperature=0.1, max_tokens=30)
            
            if response.success:
                print(f"✅ {model}: {response.content.strip()}")
            else:
                print(f"❌ {model}: {response.error_message}")
                
        except Exception as e:
            print(f"❌ {model}: 錯誤 - {e}")

if __name__ == "__main__":
    print("🚀 OpenRouter 官方測試開始")
    print("=" * 50)
    
    # 基本 API 測試
    basic_test_success = test_openrouter_official()
    
    # 模型測試
    if basic_test_success:
        test_openrouter_models()
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果:")
    print(f"   - 基本 API: {'✅ 通過' if basic_test_success else '❌ 失敗'}")
    
    if basic_test_success:
        print("\n🎉 OpenRouter API 配置成功！根據官方文檔測試通過！")
    else:
        print("\n❌ OpenRouter API 配置失敗，請檢查配置和網路連接。")