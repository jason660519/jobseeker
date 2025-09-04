#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM指令遵循與結構化輸出標準庫 - 演示腳本

注意：模擬LLM相關功能已被移除。
要使用此演示腳本，請配置真實的LLM API密鑰。

支持的LLM提供商：
- OpenAI (設置 OPENAI_API_KEY)
- Anthropic Claude (設置 ANTHROPIC_API_KEY)
- OpenRouter (設置 OPENROUTER_API_KEY)

使用方法:
    1. 設置相應的API密鑰環境變量
    2. python demo_llm_standard.py
"""

import os
import sys

def main():
    """主函數"""
    print("=" * 60)
    print("LLM標準庫演示腳本")
    print("=" * 60)
    print()
    print("⚠️  注意：模擬LLM功能已被移除")
    print()
    print("要使用此演示腳本，請先配置以下任一API密鑰：")
    print("• OPENAI_API_KEY - OpenAI GPT模型")
    print("• ANTHROPIC_API_KEY - Anthropic Claude模型")
    print("• OPENROUTER_API_KEY - OpenRouter統一API")
    print()
    
    # 檢查是否有可用的API密鑰
    api_keys = {
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'OpenRouter': os.getenv('OPENROUTER_API_KEY')
    }
    
    available_keys = [name for name, key in api_keys.items() if key]
    
    if available_keys:
        print(f"✅ 檢測到可用的API密鑰: {', '.join(available_keys)}")
        print("💡 您可以開始使用真實的LLM服務進行開發")
    else:
        print("❌ 未檢測到任何API密鑰")
        print("💡 請設置環境變量後重新運行此腳本")
    
    print()
    print("目前LLM服務暫時不可用，請使用主頁的智能職位搜尋功能。")
    print("=" * 60)

if __name__ == '__main__':
    main()