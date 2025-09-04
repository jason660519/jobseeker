#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM API客戶端
支持多種LLM提供商的統一API調用接口

Author: jobseeker Team
Date: 2025-01-27
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod

from .llm_config import LLMProvider, LLMConfig


@dataclass
class LLMResponse:
    """LLM響應結果"""
    content: str
    usage: Dict[str, Any]
    model: str
    provider: LLMProvider
    response_time: float
    success: bool = True
    error_message: Optional[str] = None


class BaseLLMClient(ABC):
    """LLM客戶端基類"""
    
    def __init__(self, config: LLMConfig):
        """初始化客戶端"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用LLM API"""
        pass
    
    @abstractmethod
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """異步調用LLM API"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI客戶端"""
    
    def __init__(self, config: LLMConfig):
        """初始化OpenAI客戶端"""
        super().__init__(config)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客戶端"""
        try:
            # 嘗試導入OpenAI庫
            import openai
            
            # 根據提供商設置不同的配置
            client_kwargs = {
                "api_key": self.config.api_key,
                "timeout": self.config.timeout
            }
            
            # 如果是 OpenRouter，設置特定的 base_url 和 headers
            if self.config.provider == LLMProvider.OPENROUTER:
                client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
                # OpenRouter 需要特定的 headers
                client_kwargs["default_headers"] = {
                    "HTTP-Referer": "https://github.com/your-repo/jobseeker",  # 可選：您的網站 URL
                    "X-Title": "JobSeeker"  # 可選：您的應用名稱
                }
            elif self.config.api_base:
                client_kwargs["base_url"] = self.config.api_base
            
            # 初始化客戶端
            self.client = openai.OpenAI(**client_kwargs)
            
            provider_name = "OpenRouter" if self.config.provider == LLMProvider.OPENROUTER else "OpenAI"
            self.logger.info(f"{provider_name}客戶端初始化成功: {self.config.model_name}")
            
        except ImportError:
            self.logger.warning("OpenAI庫未安裝，請運行: pip install openai")
            self.client = None
        except Exception as e:
            self.logger.error(f"OpenAI客戶端初始化失敗: {e}")
            self.client = None
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用OpenAI API"""
        if not self.client:
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=0.0,
                success=False,
                error_message="OpenAI客戶端未初始化"
            )
        
        start_time = time.time()
        
        try:
            # 準備請求參數
            request_params = {
                "model": self.config.model_name,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
            }
            
            # 只有在明確要求 JSON 格式時才添加 response_format
            if "response_format" in kwargs:
                request_params["response_format"] = kwargs["response_format"]
            
            # 調用API
            response = self.client.chat.completions.create(**request_params)
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.model_dump() if response.usage else {},
                model=response.model,
                provider=self.config.provider,
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"OpenAI API調用失敗: {e}")
            
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=False,
                error_message=str(e)
            )
    
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """異步調用OpenAI API"""
        # 在實際實現中，這裡應該使用異步版本的OpenAI客戶端
        # 目前使用同步版本的包裝
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.call, messages, **kwargs)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude客戶端"""
    
    def __init__(self, config: LLMConfig):
        """初始化Anthropic客戶端"""
        super().__init__(config)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化Anthropic客戶端"""
        try:
            # 嘗試導入Anthropic庫
            import anthropic
            
            # 初始化客戶端
            self.client = anthropic.Anthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            
            self.logger.info(f"Anthropic客戶端初始化成功: {self.config.model_name}")
            
        except ImportError:
            self.logger.warning("Anthropic庫未安裝，請運行: pip install anthropic")
            self.client = None
        except Exception as e:
            self.logger.error(f"Anthropic客戶端初始化失敗: {e}")
            self.client = None
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用Anthropic API"""
        if not self.client:
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=0.0,
                success=False,
                error_message="Anthropic客戶端未初始化"
            )
        
        start_time = time.time()
        
        try:
            # 轉換消息格式（Anthropic格式略有不同）
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            # 調用API
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message,
                messages=user_messages
            )
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.content[0].text,
                usage=response.usage.model_dump() if hasattr(response, 'usage') else {},
                model=response.model,
                provider=self.config.provider,
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Anthropic API調用失敗: {e}")
            
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=False,
                error_message=str(e)
            )
    
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """異步調用Anthropic API"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.call, messages, **kwargs)


class GoogleClient(BaseLLMClient):
    """Google AI Studio客戶端"""
    
    def __init__(self, config: LLMConfig):
        """初始化Google客戶端"""
        super().__init__(config)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化Google客戶端"""
        try:
            # 嘗試導入Google AI庫
            import google.generativeai as genai
            
            # 配置API密鑰
            genai.configure(api_key=self.config.api_key)
            
            # 初始化模型
            self.client = genai.GenerativeModel(self.config.model_name)
            
            self.logger.info(f"Google客戶端初始化成功: {self.config.model_name}")
            
        except ImportError:
            self.logger.warning("Google AI庫未安裝，請運行: pip install google-generativeai")
            self.client = None
        except Exception as e:
            self.logger.error(f"Google客戶端初始化失敗: {e}")
            self.client = None
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用Google AI API"""
        if not self.client:
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=0.0,
                success=False,
                error_message="Google客戶端未初始化"
            )
        
        start_time = time.time()
        
        try:
            # 將消息轉換為Google格式
            prompt = self._convert_messages_to_prompt(messages)
            
            # 調用API
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': self.config.temperature,
                    'max_output_tokens': self.config.max_tokens,
                }
            )
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.text,
                usage={
                    'prompt_tokens': 0,  # Google API不提供詳細token統計
                    'completion_tokens': 0,
                    'total_tokens': 0
                },
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Google API調用失敗: {e}")
            
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=False,
                error_message=str(e)
            )
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """將消息列表轉換為Google格式的提示"""
        prompt_parts = []
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts)
    
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """異步調用Google AI API"""
        # Google AI庫目前不支持異步，使用同步調用
        return self.call(messages, **kwargs)


class DeepseekerClient(BaseLLMClient):
    """Deepseeker客戶端"""
    
    def __init__(self, config: LLMConfig):
        """初始化Deepseeker客戶端"""
        super().__init__(config)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化Deepseeker客戶端"""
        try:
            # 使用OpenAI兼容的API
            import openai
            
            # 初始化客戶端
            self.client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url="https://api.deepseek.com",
                timeout=self.config.timeout
            )
            
            self.logger.info(f"Deepseeker客戶端初始化成功: {self.config.model_name}")
            
        except ImportError:
            self.logger.warning("OpenAI庫未安裝，請運行: pip install openai")
            self.client = None
        except Exception as e:
            self.logger.error(f"Deepseeker客戶端初始化失敗: {e}")
            self.client = None
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """調用Deepseeker API"""
        if not self.client:
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=0.0,
                success=False,
                error_message="Deepseeker客戶端未初始化"
            )
        
        start_time = time.time()
        
        try:
            # 準備請求參數
            request_params = {
                'model': self.config.model_name,
                'messages': messages,
                'temperature': self.config.temperature,
                'max_tokens': self.config.max_tokens,
                **kwargs
            }
            
            # 調用API
            response = self.client.chat.completions.create(**request_params)
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.model_dump() if response.usage else {},
                model=response.model,
                provider=self.config.provider,
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Deepseeker API調用失敗: {e}")
            
            return LLMResponse(
                content="",
                usage={},
                model=self.config.model_name,
                provider=self.config.provider,
                response_time=response_time,
                success=False,
                error_message=str(e)
            )
    
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """異步調用Deepseeker API"""
        # 使用asyncio在線程池中運行同步調用
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.call, messages, **kwargs)


# MockLLMClient 已移除 - 不再支持模擬LLM功能


class LLMClientFactory:
    """LLM客戶端工廠"""
    
    @staticmethod
    def create_client(config: LLMConfig) -> BaseLLMClient:
        """
        根據配置創建對應的LLM客戶端
        
        Args:
            config: LLM配置
            
        Returns:
            BaseLLMClient: LLM客戶端實例
            
        Raises:
            ValueError: 當提供商不支持或配置無效時
        """
        if config.provider in [LLMProvider.OPENAI, LLMProvider.AZURE_OPENAI, LLMProvider.OPENROUTER]:
            return OpenAIClient(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(config)
        elif config.provider == LLMProvider.GOOGLE:
            return GoogleClient(config)
        elif config.provider == LLMProvider.DEEPSEEKER:
            return DeepseekerClient(config)
        else:
            raise ValueError(f"不支持的LLM提供商: {config.provider}。目前LLM服務暫時不可用，請使用主頁的智能職位搜尋功能，這將幫助您更精準地找到理想工作。")


# 便捷函數
def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """
    創建LLM客戶端的便捷函數
    
    Args:
        config: LLM配置
        
    Returns:
        BaseLLMClient: LLM客戶端實例
    """
    return LLMClientFactory.create_client(config)