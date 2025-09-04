#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM意圖分析器配置管理
管理不同LLM提供商的配置、API密鑰和參數設置

Author: jobseeker Team
Date: 2025-01-27
"""

import os
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """LLM提供商枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    DEEPSEEKER = "deepseeker"
    LOCAL_LLAMA = "local_llama"
    OPENROUTER = "openrouter"


@dataclass
class LLMConfig:
    """LLM配置類"""
    provider: LLMProvider
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout: int = 30
    retry_attempts: int = 3
    enable_cache: bool = True
    fallback_to_basic: bool = True
    
    # 成本控制
    max_requests_per_hour: int = 1000
    max_cost_per_day: float = 10.0  # USD
    
    # 性能設置
    async_processing: bool = False
    batch_processing: bool = False
    
    def __post_init__(self):
        """後初始化處理"""
        # 從環境變量獲取API密鑰
        if not self.api_key:
            self.api_key = self._get_api_key_from_env()
        
        # 設置默認模型名稱
        if not self.model_name:
            self.model_name = self._get_default_model_name()
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """從環境變量獲取API密鑰"""
        env_key_map = {
            LLMProvider.OPENAI: ["OPENAI_API_KEY", "jobseeker_OPENAI_API_KEY"],
            LLMProvider.ANTHROPIC: ["ANTHROPIC_API_KEY", "jobseeker_ANTHROPIC_API_KEY"],
            LLMProvider.GOOGLE: ["GOOGLE_AI_STUDIO_API_KEY", "jobseeker_GOOGLE_API_KEY"],
            LLMProvider.AZURE_OPENAI: ["AZURE_OPENAI_API_KEY", "jobseeker_AZURE_OPENAI_API_KEY"],
            LLMProvider.DEEPSEEKER: ["DEEPSEEKER_API_KEY", "jobseeker_DEEPSEEKER_API_KEY"],
            LLMProvider.OPENROUTER: ["OPENROUTER_API_KEY", "jobseeker_OPENROUTER_API_KEY"],
            LLMProvider.LOCAL_LLAMA: None
        }
        
        env_keys = env_key_map.get(self.provider)
        if env_keys:
            for key in env_keys:
                api_key = os.getenv(key)
                if api_key:
                    return api_key
        return None
    
    def _get_default_model_name(self) -> str:
        """獲取默認模型名稱"""
        # 優先從環境變數獲取模型名稱
        env_model_key = f"jobseeker_{self.provider.value.upper()}_MODEL"
        env_model = os.getenv(env_model_key)
        if env_model:
            return env_model
            
        model_map = {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            LLMProvider.GOOGLE: "gemini-1.5-flash",
            LLMProvider.AZURE_OPENAI: "gpt-35-turbo",
            LLMProvider.DEEPSEEKER: "deepseek-chat",
            LLMProvider.OPENROUTER: "openai/gpt-4o-mini",
            LLMProvider.LOCAL_LLAMA: "llama-3-8b-instruct"
        }
        
        return model_map.get(self.provider, "unknown")
    
    def is_valid(self) -> bool:
        """檢查配置是否有效"""
        # 本地模式不需要API密鑰
        if self.provider == LLMProvider.LOCAL_LLAMA:
            return True
        
        # 其他模式需要API密鑰
        return bool(self.api_key)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "enable_cache": self.enable_cache,
            "fallback_to_basic": self.fallback_to_basic,
            "max_requests_per_hour": self.max_requests_per_hour,
            "max_cost_per_day": self.max_cost_per_day,
            "async_processing": self.async_processing,
            "batch_processing": self.batch_processing,
            "has_api_key": bool(self.api_key)
        }


class LLMConfigManager:
    """LLM配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.configs = self._load_default_configs()
        self.enable_random_selection = os.getenv("jobseeker_LLM_RANDOM_SELECTION", "false").lower() == "true"
        
        # 設置默認提供商
        default_provider_name = os.getenv("jobseeker_DEFAULT_LLM_PROVIDER", "openrouter").lower()
        try:
            self.current_provider = LLMProvider(default_provider_name)
        except ValueError:
            self.current_provider = LLMProvider.OPENROUTER
    
    def _load_default_configs(self) -> Dict[LLMProvider, LLMConfig]:
        """加載默認配置"""
        configs = {}
        
        # OpenAI 配置
        configs[LLMProvider.OPENAI] = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4o-mini",
            temperature=float(os.getenv("jobseeker_OPENAI_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("jobseeker_OPENAI_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("jobseeker_OPENAI_TIMEOUT", "30")),
            max_requests_per_hour=500,
            max_cost_per_day=10.0
        )
        
        # Anthropic 配置
        configs[LLMProvider.ANTHROPIC] = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            temperature=float(os.getenv("jobseeker_ANTHROPIC_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("jobseeker_ANTHROPIC_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("jobseeker_ANTHROPIC_TIMEOUT", "30")),
            max_requests_per_hour=200,
            max_cost_per_day=15.0
        )
        
        # Google 配置
        configs[LLMProvider.GOOGLE] = LLMConfig(
            provider=LLMProvider.GOOGLE,
            model_name="gemini-1.5-flash",
            temperature=float(os.getenv("jobseeker_GOOGLE_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("jobseeker_GOOGLE_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("jobseeker_GOOGLE_TIMEOUT", "30")),
            max_requests_per_hour=300,
            max_cost_per_day=8.0
        )
        
        # Azure OpenAI 配置
        configs[LLMProvider.AZURE_OPENAI] = LLMConfig(
            provider=LLMProvider.AZURE_OPENAI,
            model_name="gpt-35-turbo",
            temperature=float(os.getenv("jobseeker_AZURE_OPENAI_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("jobseeker_AZURE_OPENAI_MAX_TOKENS", "800")),
            timeout=int(os.getenv("jobseeker_AZURE_OPENAI_TIMEOUT", "20")),
            max_requests_per_hour=300,
            max_cost_per_day=8.0
        )
        
        # Deepseeker 配置
        configs[LLMProvider.DEEPSEEKER] = LLMConfig(
            provider=LLMProvider.DEEPSEEKER,
            model_name="deepseek-chat",
            temperature=float(os.getenv("jobseeker_DEEPSEEKER_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("jobseeker_DEEPSEEKER_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("jobseeker_DEEPSEEKER_TIMEOUT", "30")),
            max_requests_per_hour=400,
            max_cost_per_day=5.0
        )
        
        # OpenRouter 配置
        configs[LLMProvider.OPENROUTER] = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model_name=os.getenv("jobseeker_OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            temperature=float(os.getenv("jobseeker_OPENROUTER_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("jobseeker_OPENROUTER_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("jobseeker_OPENROUTER_TIMEOUT", "30")),
            max_requests_per_hour=500,
            max_cost_per_day=8.0
        )
        
        # 本地Llama 配置
        configs[LLMProvider.LOCAL_LLAMA] = LLMConfig(
            provider=LLMProvider.LOCAL_LLAMA,
            api_base="http://localhost:8080",
            model_name="llama-3-8b-instruct",
            temperature=0.2,
            max_tokens=1000,
            timeout=60,
            max_requests_per_hour=10000,  # 本地無限制
            max_cost_per_day=0.0  # 本地無成本
        )

        
        return configs
    
    def get_config(self, provider: Optional[LLMProvider] = None) -> LLMConfig:
        """
        獲取指定提供商的配置
        
        Args:
            provider: LLM提供商，如果為None則使用當前提供商或隨機選擇
            
        Returns:
            LLMConfig: 配置對象
        """
        if provider is None:
            if self.enable_random_selection:
                provider = self.get_random_available_provider()
            else:
                provider = self.current_provider
        
        return self.configs.get(provider, self.configs[LLMProvider.OPENROUTER])
    
    def set_current_provider(self, provider: LLMProvider) -> bool:
        """
        設置當前LLM提供商
        
        Args:
            provider: LLM提供商
            
        Returns:
            bool: 是否設置成功
        """
        config = self.configs.get(provider)
        if config and config.is_valid():
            self.current_provider = provider
            return True
        return False
    
    def get_available_providers(self) -> List[LLMProvider]:
        """
        獲取可用的LLM提供商列表
        
        Returns:
            List[LLMProvider]: 可用提供商列表
        """
        available = []
        for provider, config in self.configs.items():
            if config.is_valid():
                available.append(provider)
        return available
    
    def get_random_available_provider(self) -> LLMProvider:
        """
        隨機選擇一個可用的LLM提供商
        
        Returns:
            LLMProvider: 隨機選擇的提供商
        """
        available_providers = self.get_available_providers()
        if not available_providers:
            return LLMProvider.MOCK
        
        # 排除MOCK提供商，優先選擇真實的LLM提供商
        real_providers = [p for p in available_providers if p != LLMProvider.MOCK]
        if real_providers:
            return random.choice(real_providers)
        else:
            return LLMProvider.MOCK
    
    def set_random_selection(self, enabled: bool) -> None:
        """
        設置是否啟用隨機選擇
        
        Args:
            enabled: 是否啟用隨機選擇
        """
        self.enable_random_selection = enabled
    
    def update_config(self, provider: LLMProvider, **kwargs) -> bool:
        """
        更新指定提供商的配置
        
        Args:
            provider: LLM提供商
            **kwargs: 要更新的配置項
            
        Returns:
            bool: 是否更新成功
        """
        if provider not in self.configs:
            return False
        
        config = self.configs[provider]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return True
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        獲取配置摘要
        
        Returns:
            Dict: 配置摘要
        """
        summary = {
            "current_provider": self.current_provider.value,
            "available_providers": [p.value for p in self.get_available_providers()],
            "configs": {}
        }
        
        for provider, config in self.configs.items():
            summary["configs"][provider.value] = config.to_dict()
        
        return summary
    
    def validate_all_configs(self) -> Dict[LLMProvider, bool]:
        """
        驗證所有配置
        
        Returns:
            Dict: 每個提供商的驗證結果
        """
        validation_results = {}
        for provider, config in self.configs.items():
            validation_results[provider] = config.is_valid()
        return validation_results


# 全局配置管理器實例
config_manager = LLMConfigManager()


def get_current_llm_config() -> LLMConfig:
    """
    獲取當前LLM配置的便捷函數
    
    Returns:
        LLMConfig: 當前配置
    """
    return config_manager.get_config()


def set_llm_provider(provider: LLMProvider) -> bool:
    """
    設置LLM提供商的便捷函數
    
    Args:
        provider: LLM提供商
        
    Returns:
        bool: 是否設置成功
    """
    return config_manager.set_current_provider(provider)


def get_available_llm_providers() -> List[LLMProvider]:
    """
    獲取可用LLM提供商的便捷函數
    
    Returns:
        List[LLMProvider]: 可用提供商列表
    """
    return config_manager.get_available_providers()