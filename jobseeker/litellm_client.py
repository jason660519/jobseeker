#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiteLL M統一客戶端
使用LiteLLM提供統一的多LLM提供商支持

Author: jobseeker Team
Date: 2025-01-27
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import os

try:
    import litellm
    from litellm import completion, acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None

from .llm_config import LLMProvider, LLMConfig
from .llm_client import LLMResponse, BaseLLMClient


class LiteLLMClient(BaseLLMClient):
    """LiteLLM統一客戶端 - 支持多種LLM提供商"""
    
    def __init__(self, config: LLMConfig):
        """初始化LiteLLM客戶端"""
        super().__init__(config)
        self.model_name = self._get_litellm_model_name()
        self._setup_environment()
        
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM未安裝，請運行: pip install litellm")
        
        # 設置LiteLLM日誌級別
        litellm.set_verbose = False
        
        self.logger.info(f"LiteLLM客戶端初始化成功: {self.model_name}")
    
    def _get_litellm_model_name(self) -> str:
        """獲取LiteLLM格式的模型名稱"""
        provider_model_map = {
            LLMProvider.OPENAI: "gpt-3.5-turbo",  # OpenAI不需要前綴
            LLMProvider.ANTHROPIC: "anthropic/claude-3-sonnet-20240229",
            LLMProvider.GOOGLE: "gemini/gemini-1.5-flash",
            LLMProvider.AZURE_OPENAI: f"azure/{self.config.model_name or 'gpt-35-turbo'}",
            LLMProvider.DEEPSEEKER: "deepseek/deepseek-chat",
            LLMProvider.LOCAL_LLAMA: "ollama/llama2",
            LLMProvider.MOCK: "gpt-3.5-turbo"  # 用於測試
        }
        
        # 如果配置中指定了模型名稱，優先使用
        if self.config.model_name and self.config.provider == LLMProvider.OPENAI:
            return self.config.model_name
        
        return provider_model_map.get(self.config.provider, "gpt-3.5-turbo")
    
    def _setup_environment(self):
        """設置環境變量"""
        # 設置API密鑰到環境變量（LiteLLM會自動讀取）
        if self.config.api_key:
            if self.config.provider == LLMProvider.OPENAI:
                os.environ["OPENAI_API_KEY"] = self.config.api_key
            elif self.config.provider == LLMProvider.ANTHROPIC:
                os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
            elif self.config.provider == LLMProvider.GOOGLE:
                os.environ["GOOGLE_AI_STUDIO_API_KEY"] = self.config.api_key
            elif self.config.provider == LLMProvider.AZURE_OPENAI:
                os.environ["AZURE_API_KEY"] = self.config.api_key
                if self.config.api_base:
                    os.environ["AZURE_API_BASE"] = self.config.api_base
            elif self.config.provider == LLMProvider.DEEPSEEKER:
                os.environ["DEEPSEEK_API_KEY"] = self.config.api_key
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用LLM API（同步）"""
        start_time = time.time()
        
        try:
            # 準備請求參數
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "timeout": self.config.timeout
            }
            
            # 處理response_format參數
            response_format = kwargs.get("response_format")
            if response_format and response_format.get("type") == "json_object":
                # 對於支持JSON模式的模型
                if "gpt" in self.model_name.lower():
                    request_params["response_format"] = {"type": "json_object"}
                else:
                    # 對於不支持JSON模式的模型，在消息中添加JSON指令
                    if messages and messages[-1]["role"] == "user":
                        messages[-1]["content"] += "\n\n請以有效的JSON格式回應。"
            
            # 調用LiteLLM
            response = completion(**request_params)
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.__dict__ if response.usage else {},
                model=response.model,
                provider=self.config.provider,
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"LiteLLM API調用失敗: {error_msg}")
            
            return LLMResponse(
                content="",
                usage={},
                model=self.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=False,
                error_message=error_msg
            )
    
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用LLM API（異步）"""
        start_time = time.time()
        
        try:
            # 準備請求參數
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "timeout": self.config.timeout
            }
            
            # 處理response_format參數
            response_format = kwargs.get("response_format")
            if response_format and response_format.get("type") == "json_object":
                if "gpt" in self.model_name.lower():
                    request_params["response_format"] = {"type": "json_object"}
                else:
                    if messages and messages[-1]["role"] == "user":
                        messages[-1]["content"] += "\n\n請以有效的JSON格式回應。"
            
            # 異步調用LiteLLM
            response = await acompletion(**request_params)
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.__dict__ if response.usage else {},
                model=response.model,
                provider=self.config.provider,
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"LiteLLM異步API調用失敗: {error_msg}")
            
            return LLMResponse(
                content="",
                usage={},
                model=self.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=False,
                error_message=error_msg
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """測試LLM連接"""
        test_messages = [
            {
                "role": "system",
                "content": "你是一個測試助手。"
            },
            {
                "role": "user",
                "content": "請回應'連接測試成功'並以JSON格式返回: {\"status\": \"success\", \"message\": \"連接測試成功\"}"
            }
        ]
        
        try:
            response = self.call(
                messages=test_messages,
                temperature=0.1,
                max_tokens=100,
                response_format={"type": "json_object"}
            )
            
            if response.success:
                try:
                    # 嘗試解析JSON響應
                    json_response = json.loads(response.content)
                    return {
                        "success": True,
                        "provider": self.config.provider.value,
                        "model": response.model,
                        "response_time": response.response_time,
                        "usage": response.usage,
                        "test_response": json_response
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "provider": self.config.provider.value,
                        "model": response.model,
                        "response_time": response.response_time,
                        "usage": response.usage,
                        "test_response": response.content,
                        "warning": "響應不是有效的JSON格式"
                    }
            else:
                return {
                    "success": False,
                    "provider": self.config.provider.value,
                    "model": self.model_name,
                    "error": response.error_message
                }
                
        except Exception as e:
            return {
                "success": False,
                "provider": self.config.provider.value,
                "model": self.model_name,
                "error": str(e)
            }


def create_litellm_client(config: LLMConfig) -> LiteLLMClient:
    """創建LiteLLM客戶端"""
    return LiteLLMClient(config)


def test_multiple_providers(api_keys: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """測試多個LLM提供商的連接"""
    results = {}
    
    # 測試配置 - 使用LiteLLM標準格式和可用模型
    test_configs = {
        "openai": (LLMProvider.OPENAI, "gpt-3.5-turbo"),
        "anthropic": (LLMProvider.ANTHROPIC, "anthropic/claude-3-haiku-20240307"),
        "google": (LLMProvider.GOOGLE, "gemini/gemini-pro"),
        "deepseeker": (LLMProvider.DEEPSEEKER, "deepseek/deepseek-chat")
    }
    
    for provider_name, (provider, model_name) in test_configs.items():
        api_key = api_keys.get(provider_name)
        if not api_key:
            results[provider.value] = {
                "success": False,
                "error": "API密鑰未提供"
            }
            continue
        
        try:
            config = LLMConfig(
                provider=provider,
                api_key=api_key,
                model_name=model_name,
                temperature=0.1,
                max_tokens=100
            )
            
            client = create_litellm_client(config)
            test_result = client.test_connection()
            results[provider.value] = test_result
            
        except Exception as e:
            results[provider.value] = {
                "success": False,
                "error": str(e)
            }
    
    return results