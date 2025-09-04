#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiteLLM Docker 代理服務器測試腳本
用於測試通過Docker部署的LiteLLM代理服務器功能
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class LiteLLMDockerClient:
    """
    LiteLLM Docker 代理客戶端
    用於與Docker部署的LiteLLM代理服務器進行通信
    """
    
    def __init__(self, base_url: str = "http://localhost:4000", master_key: Optional[str] = None):
        """
        初始化客戶端
        
        Args:
            base_url: LiteLLM代理服務器的基礎URL
            master_key: 主密鑰（如果設置了的話）
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
        if master_key:
            self.headers["Authorization"] = f"Bearer {master_key}"
    
    def health_check(self) -> Dict[str, Any]:
        """
        檢查代理服務器健康狀態
        
        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=10)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def list_models(self) -> Dict[str, Any]:
        """
        獲取可用模型列表
        
        Returns:
            Dict[str, Any]: 模型列表
        """
        try:
            response = requests.get(f"{self.base_url}/v1/models", headers=self.headers, timeout=10)
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "models": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def chat_completion(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """
        發送聊天完成請求
        
        Args:
            model: 模型名稱
            messages: 消息列表
            **kwargs: 其他參數
        
        Returns:
            Dict[str, Any]: 聊天完成結果
        """
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

def test_litellm_docker_proxy():
    """
    測試LiteLLM Docker代理服務器功能
    """
    print("=" * 60)
    print("🐳 LiteLLM Docker 代理服務器測試")
    print("=" * 60)
    
    # 初始化客戶端
    client = LiteLLMDockerClient(
        base_url="http://localhost:4000",
        master_key="sk-litellm-master-key"
    )
    
    # 1. 健康檢查
    print("\n🏥 1. 健康檢查")
    print("-" * 40)
    health = client.health_check()
    if health["status"] == "healthy":
        print("✅ 代理服務器運行正常")
        print(f"📊 響應: {health.get('response', 'N/A')}")
    else:
        print("❌ 代理服務器不可用")
        print(f"🔍 錯誤: {health.get('error', 'Unknown error')}")
        print("\n💡 請確保Docker容器正在運行:")
        print("   docker-compose -f docker-compose.litellm.yml up -d")
        return
    
    # 2. 獲取模型列表
    print("\n📋 2. 可用模型列表")
    print("-" * 40)
    models_result = client.list_models()
    if models_result["status"] == "success":
        models = models_result["models"].get("data", [])
        print(f"✅ 找到 {len(models)} 個可用模型:")
        for model in models[:5]:  # 只顯示前5個
            print(f"   📝 {model.get('id', 'Unknown')}")
        if len(models) > 5:
            print(f"   ... 還有 {len(models) - 5} 個模型")
    else:
        print("❌ 無法獲取模型列表")
        print(f"🔍 錯誤: {models_result.get('error', 'Unknown error')}")
    
    # 3. 測試聊天完成
    print("\n💬 3. 聊天完成測試")
    print("-" * 40)
    
    test_models = ["claude-3-haiku", "deepseek-chat", "gpt-3.5-turbo"]
    test_message = "你好，請用一句話介紹你自己。"
    
    for model in test_models:
        print(f"\n🤖 測試模型: {model}")
        result = client.chat_completion(
            model=model,
            messages=[{"role": "user", "content": test_message}],
            max_tokens=100,
            temperature=0.7
        )
        
        if result["status"] == "success":
            response_content = result["response"]["choices"][0]["message"]["content"]
            print(f"✅ 回應: {response_content[:100]}{'...' if len(response_content) > 100 else ''}")
        else:
            print(f"❌ 失敗: {result.get('error', 'Unknown error')[:100]}")
    
    # 4. 性能測試
    print("\n⚡ 4. 性能測試")
    print("-" * 40)
    
    start_time = time.time()
    concurrent_requests = 3
    successful_requests = 0
    
    for i in range(concurrent_requests):
        result = client.chat_completion(
            model="claude-3-haiku",
            messages=[{"role": "user", "content": f"測試請求 #{i+1}"}],
            max_tokens=50
        )
        if result["status"] == "success":
            successful_requests += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"📊 完成 {concurrent_requests} 個請求")
    print(f"✅ 成功: {successful_requests}/{concurrent_requests}")
    print(f"⏱️  總時間: {duration:.2f} 秒")
    print(f"🚀 平均響應時間: {duration/concurrent_requests:.2f} 秒/請求")
    
    # 5. 總結
    print("\n📊 5. 測試總結")
    print("=" * 60)
    print("✅ LiteLLM Docker代理服務器測試完成")
    print("🎯 主要功能:")
    print("   • 統一API接口調用多個LLM提供商")
    print("   • 支援負載均衡和故障轉移")
    print("   • 提供標準OpenAI格式的響應")
    print("   • 支援速率限制和使用監控")
    print("\n🔗 代理服務器地址: http://localhost:4000")
    print("📚 API文檔: http://localhost:4000/docs")
    print("\n" + "=" * 60)

def main():
    """
    主函數
    """
    try:
        test_litellm_docker_proxy()
    except KeyboardInterrupt:
        print("\n\n⏹️  測試被用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()