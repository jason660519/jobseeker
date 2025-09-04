#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查所有雲端LLM API的真實可用狀態
不包含模擬或本地服務，只檢查真實的雲端API
"""

import os
import sys
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

def test_provider_connection(provider: LLMProvider) -> dict:
    """
    測試單個LLM提供商的連接狀態
    
    Args:
        provider: LLM提供商
        
    Returns:
        dict: 測試結果
    """
    result = {
        'provider': provider.value,
        'has_api_key': False,
        'config_valid': False,
        'connection_success': False,
        'error_message': None,
        'response_time': None,
        'model_used': None
    }
    
    try:
        # 獲取配置
        config = config_manager.get_config(provider)
        
        # 檢查API密鑰
        if config.api_key:
            result['has_api_key'] = True
            result['model_used'] = config.model_name
        else:
            result['error_message'] = "API密鑰未設置"
            return result
            
        # 檢查配置有效性
        if config.is_valid():
            result['config_valid'] = True
        else:
            result['error_message'] = "配置無效"
            return result
            
        # 測試實際連接
        client = create_llm_client(config)
        
        # 發送簡單測試請求
        test_messages = [
            {"role": "user", "content": "Hello, please respond with just 'OK'"}
        ]
        
        import time
        start_time = time.time()
        response = client.call(test_messages, temperature=0.1, max_tokens=10)
        end_time = time.time()
        
        result['response_time'] = round(end_time - start_time, 2)
        
        if response.success:
            result['connection_success'] = True
        else:
            result['error_message'] = response.error_message
            
    except Exception as e:
        result['error_message'] = str(e)
        
    return result

def check_all_cloud_llm_status():
    """
    檢查所有雲端LLM API的狀態
    """
    print("🔍 檢查所有雲端LLM API的真實可用狀態...")
    print("=" * 60)
    
    # 定義雲端LLM提供商（排除本地和模擬服務）
    cloud_providers = [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC, 
        LLMProvider.GOOGLE,
        LLMProvider.AZURE_OPENAI,
        LLMProvider.DEEPSEEKER,
        LLMProvider.OPENROUTER
    ]
    
    available_count = 0
    total_tested = 0
    results = []
    
    for provider in cloud_providers:
        print(f"\n🧪 測試 {provider.value.upper()}...")
        total_tested += 1
        
        result = test_provider_connection(provider)
        results.append(result)
        
        # 顯示結果
        if result['connection_success']:
            print(f"✅ {provider.value.upper()}: 可用")
            print(f"   📊 模型: {result['model_used']}")
            print(f"   ⏱️ 響應時間: {result['response_time']}秒")
            available_count += 1
        elif result['has_api_key'] and result['config_valid']:
            print(f"❌ {provider.value.upper()}: 連接失敗")
            print(f"   🚫 錯誤: {result['error_message']}")
        elif result['has_api_key']:
            print(f"⚠️ {provider.value.upper()}: 配置無效")
            print(f"   🚫 錯誤: {result['error_message']}")
        else:
            print(f"⭕ {provider.value.upper()}: 未配置")
            print(f"   📝 狀態: {result['error_message']}")
    
    # 總結報告
    print("\n" + "=" * 60)
    print("📊 **雲端LLM API狀態總結**")
    print(f"🔢 總共測試: {total_tested} 個雲端LLM提供商")
    print(f"✅ 可正常使用: {available_count} 個")
    print(f"❌ 不可用: {total_tested - available_count} 個")
    print(f"📈 可用率: {(available_count/total_tested*100):.1f}%")
    
    # 詳細狀態列表
    print("\n📋 **詳細狀態列表:**")
    for result in results:
        status = "✅ 可用" if result['connection_success'] else "❌ 不可用"
        print(f"   • {result['provider'].upper()}: {status}")
        if result['connection_success']:
            print(f"     - 模型: {result['model_used']}")
            print(f"     - 響應時間: {result['response_time']}秒")
        elif result['error_message']:
            print(f"     - 原因: {result['error_message']}")
    
    return available_count, total_tested, results

if __name__ == "__main__":
    available, total, results = check_all_cloud_llm_status()
    
    print("\n" + "=" * 60)
    if available > 0:
        print(f"🎉 結論: 目前有 **{available}** 個雲端LLM API處於可正常使用狀態")
    else:
        print("⚠️ 結論: 目前沒有可用的雲端LLM API")
        print("💡 建議: 請檢查API密鑰配置或網路連接")