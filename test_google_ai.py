#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Generative AI 測試腳本
測試 Google AI 的基本功能，包括初始化客戶端和發送生成請求
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

import google.generativeai as genai
import time

def test_google_ai_setup():
    """
    測試 Google AI 的基本設置和配置
    
    Returns:
        bool: 設置是否成功
    """
    print("🔧 測試 Google AI 設置...")
    
    # 檢查 API 密鑰
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('jobseeker_GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ Google AI API 密鑰未設置")
        print("💡 請在 .env 文件中設置 GOOGLE_API_KEY 或 jobseeker_GOOGLE_API_KEY")
        return False
    
    try:
        # 配置 API 密鑰
        genai.configure(api_key=api_key)
        print(f"✅ API 密鑰已配置 (長度: {len(api_key)} 字符)")
        return True
        
    except Exception as e:
        print(f"❌ 配置 API 密鑰時發生錯誤: {e}")
        return False

def test_list_models():
    """
    測試列出可用的模型
    
    Returns:
        list: 可用模型列表
    """
    print("\n📋 獲取可用模型列表...")
    
    try:
        models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                models.append(model.name)
                print(f"   • {model.name}")
        
        print(f"✅ 找到 {len(models)} 個支持內容生成的模型")
        return models
        
    except Exception as e:
        print(f"❌ 獲取模型列表時發生錯誤: {e}")
        return []

def test_simple_generation(model_name='gemini-pro'):
    """
    測試簡單的文本生成
    
    Args:
        model_name (str): 要使用的模型名稱
        
    Returns:
        bool: 生成是否成功
    """
    print(f"\n🧪 測試文本生成 (模型: {model_name})...")
    
    try:
        # 初始化模型
        model = genai.GenerativeModel(model_name)
        
        # 發送簡單請求
        prompt = "Please answer in one sentence: What is artificial intelligence?"
        print(f"📝 提示: {prompt}")
        
        start_time = time.time()
        response = model.generate_content(prompt)
        end_time = time.time()
        
        response_time = round(end_time - start_time, 2)
        
        if response.text:
            print(f"✅ 生成成功 (響應時間: {response_time}秒)")
            print(f"📄 回應: {response.text.strip()}")
            return True
        else:
            print("❌ 生成失敗: 沒有收到回應文本")
            return False
            
    except Exception as e:
        print(f"❌ 文本生成時發生錯誤: {e}")
        return False

def test_conversation():
    """
    測試對話功能
    
    Returns:
        bool: 對話測試是否成功
    """
    print("\n💬 測試對話功能...")
    
    try:
        # 初始化模型
        model = genai.GenerativeModel('gemini-pro')
        
        # 開始對話
        chat = model.start_chat(history=[])
        
        # 第一輪對話
        message1 = "你好，我是測試用戶"
        print(f"👤 用戶: {message1}")
        
        response1 = chat.send_message(message1)
        print(f"🤖 AI: {response1.text.strip()}")
        
        # 第二輪對話
        message2 = "請記住我剛才說的話，然後告訴我你記住了什麼"
        print(f"👤 用戶: {message2}")
        
        response2 = chat.send_message(message2)
        print(f"🤖 AI: {response2.text.strip()}")
        
        print("✅ 對話測試成功")
        return True
        
    except Exception as e:
        print(f"❌ 對話測試時發生錯誤: {e}")
        return False

def test_safety_settings():
    """
    測試安全設置功能
    
    Returns:
        bool: 安全設置測試是否成功
    """
    print("\n🛡️ 測試安全設置...")
    
    try:
        # 配置安全設置
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # 初始化帶安全設置的模型
        model = genai.GenerativeModel(
            'gemini-pro',
            safety_settings=safety_settings
        )
        
        # 測試正常內容
        response = model.generate_content("請介紹一下機器學習的基本概念")
        
        if response.text:
            print("✅ 安全設置配置成功，正常內容可以生成")
            return True
        else:
            print("⚠️ 安全設置可能過於嚴格，正常內容被阻止")
            return False
            
    except Exception as e:
        print(f"❌ 安全設置測試時發生錯誤: {e}")
        return False

def main():
    """
    主測試函數
    """
    print("🚀 Google Generative AI 完整測試開始")
    print("=" * 60)
    
    # 測試結果統計
    test_results = {
        'setup': False,
        'models': False,
        'generation': False,
        'conversation': False,
        'safety': False
    }
    
    # 1. 測試基本設置
    test_results['setup'] = test_google_ai_setup()
    
    if not test_results['setup']:
        print("\n❌ 基本設置失敗，無法繼續測試")
        return
    
    # 2. 測試模型列表
    models = test_list_models()
    test_results['models'] = len(models) > 0
    
    # 3. 測試文本生成
    if models:
        # 使用第一個可用模型進行測試
        model_to_test = models[0] if models else 'gemini-pro'
        test_results['generation'] = test_simple_generation(model_to_test)
    
    # 4. 測試對話功能
    if test_results['generation']:
        test_results['conversation'] = test_conversation()
    
    # 5. 測試安全設置
    if test_results['generation']:
        test_results['safety'] = test_safety_settings()
    
    # 總結報告
    print("\n" + "=" * 60)
    print("📊 **Google AI 測試結果總結**")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"✅ 通過測試: {passed_tests}/{total_tests}")
    print(f"📈 成功率: {(passed_tests/total_tests*100):.1f}%")
    
    print("\n📋 **詳細測試結果:**")
    test_names = {
        'setup': '基本設置',
        'models': '模型列表',
        'generation': '文本生成',
        'conversation': '對話功能',
        'safety': '安全設置'
    }
    
    for test_key, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   • {test_names[test_key]}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試通過！Google AI 已成功配置並可正常使用")
    elif passed_tests > 0:
        print("\n⚠️ 部分測試通過，Google AI 基本可用但可能需要進一步配置")
    else:
        print("\n❌ 所有測試失敗，請檢查 API 密鑰和網路連接")

if __name__ == "__main__":
    main()