"""配置管理模組"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """初始化後驗證"""
        if not self.api_key:
            raise ValueError(f"API密鑰不能為空: {self.provider}")
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens必須大於0: {self.max_tokens}")
        if not 0 <= self.temperature <= 2:
            raise ValueError(f"temperature必須在0-2之間: {self.temperature}")


@dataclass
class ValidationConfig:
    """驗證配置"""
    validate_instructions: bool = True
    validate_responses: bool = True
    strict_schema: bool = True
    allow_additional_properties: bool = False
    max_validation_errors: int = 10
    

@dataclass
class RetryConfig:
    """重試配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_timeout: bool = True
    retry_on_rate_limit: bool = True
    retry_on_server_error: bool = True
    

@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_requests: bool = False
    log_responses: bool = False
    log_tokens: bool = True
    

@dataclass
class PerformanceConfig:
    """性能配置"""
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1小時
    max_cache_size: int = 1000
    enable_metrics: bool = True
    metrics_interval: int = 60  # 60秒
    enable_profiling: bool = False
    

@dataclass
class SecurityConfig:
    """安全配置"""
    mask_api_keys: bool = True
    encrypt_cache: bool = False
    validate_ssl: bool = True
    allowed_domains: Optional[list] = None
    rate_limit_per_minute: int = 60
    

@dataclass
class StandardConfig:
    """標準庫配置"""
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'StandardConfig':
        """從文件加載配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_file.suffix}")
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardConfig':
        """從字典創建配置"""
        config = cls()
        
        # 加載模型配置
        if 'models' in data:
            for name, model_data in data['models'].items():
                config.models[name] = ModelConfig(**model_data)
        
        # 加載其他配置
        if 'validation' in data:
            config.validation = ValidationConfig(**data['validation'])
        
        if 'retry' in data:
            config.retry = RetryConfig(**data['retry'])
        
        if 'logging' in data:
            config.logging = LoggingConfig(**data['logging'])
        
        if 'performance' in data:
            config.performance = PerformanceConfig(**data['performance'])
        
        if 'security' in data:
            config.security = SecurityConfig(**data['security'])
        
        return config
    
    @classmethod
    def from_env(cls) -> 'StandardConfig':
        """從環境變量創建配置"""
        config = cls()
        
        # 從環境變量加載模型配置
        providers = ['openai', 'anthropic', 'google', 'deepseek']
        
        for provider in providers:
            api_key_env = f"{provider.upper()}_API_KEY"
            model_env = f"{provider.upper()}_MODEL"
            base_url_env = f"{provider.upper()}_BASE_URL"
            
            api_key = os.getenv(api_key_env)
            if api_key:
                model = os.getenv(model_env, cls._get_default_model(provider))
                base_url = os.getenv(base_url_env)
                
                config.models[provider] = ModelConfig(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    base_url=base_url
                )
        
        # 從環境變量加載其他配置
        if os.getenv('LLM_LOG_LEVEL'):
            config.logging.level = os.getenv('LLM_LOG_LEVEL')
        
        if os.getenv('LLM_CACHE_ENABLED'):
            config.performance.enable_caching = os.getenv('LLM_CACHE_ENABLED').lower() == 'true'
        
        if os.getenv('LLM_VALIDATE_STRICT'):
            config.validation.strict_schema = os.getenv('LLM_VALIDATE_STRICT').lower() == 'true'
        
        return config
    
    @staticmethod
    def _get_default_model(provider: str) -> str:
        """獲取提供商的默認模型"""
        defaults = {
            'openai': 'gpt-4',
            'anthropic': 'claude-3-haiku-20240307',
            'google': 'gemini-pro',
            'deepseek': 'deepseek-chat'
        }
        return defaults.get(provider, 'unknown')
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'models': {
                name: {
                    'provider': model.provider,
                    'model': model.model,
                    'api_key': '***' if self.security.mask_api_keys else model.api_key,
                    'base_url': model.base_url,
                    'max_tokens': model.max_tokens,
                    'temperature': model.temperature,
                    'timeout': model.timeout,
                    'retry_count': model.retry_count,
                    'retry_delay': model.retry_delay
                }
                for name, model in self.models.items()
            },
            'validation': {
                'validate_instructions': self.validation.validate_instructions,
                'validate_responses': self.validation.validate_responses,
                'strict_schema': self.validation.strict_schema,
                'allow_additional_properties': self.validation.allow_additional_properties,
                'max_validation_errors': self.validation.max_validation_errors
            },
            'retry': {
                'max_retries': self.retry.max_retries,
                'base_delay': self.retry.base_delay,
                'max_delay': self.retry.max_delay,
                'exponential_base': self.retry.exponential_base,
                'jitter': self.retry.jitter,
                'retry_on_timeout': self.retry.retry_on_timeout,
                'retry_on_rate_limit': self.retry.retry_on_rate_limit,
                'retry_on_server_error': self.retry.retry_on_server_error
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count,
                'log_requests': self.logging.log_requests,
                'log_responses': self.logging.log_responses,
                'log_tokens': self.logging.log_tokens
            },
            'performance': {
                'enable_caching': self.performance.enable_caching,
                'cache_ttl': self.performance.cache_ttl,
                'max_cache_size': self.performance.max_cache_size,
                'enable_metrics': self.performance.enable_metrics,
                'metrics_interval': self.performance.metrics_interval,
                'enable_profiling': self.performance.enable_profiling
            },
            'security': {
                'mask_api_keys': self.security.mask_api_keys,
                'encrypt_cache': self.security.encrypt_cache,
                'validate_ssl': self.security.validate_ssl,
                'allowed_domains': self.security.allowed_domains,
                'rate_limit_per_minute': self.security.rate_limit_per_minute
            }
        }
    
    def save_to_file(self, config_path: str):
        """保存配置到文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            if config_file.suffix.lower() == '.json':
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_file.suffix}")
    
    def get_model_config(self, provider: str) -> Optional[ModelConfig]:
        """獲取模型配置"""
        return self.models.get(provider)
    
    def add_model_config(self, name: str, config: ModelConfig):
        """添加模型配置"""
        self.models[name] = config
    
    def remove_model_config(self, name: str) -> bool:
        """移除模型配置"""
        if name in self.models:
            del self.models[name]
            return True
        return False
    
    def validate(self) -> bool:
        """驗證配置"""
        # 檢查是否至少有一個模型配置
        if not self.models:
            raise ValueError("至少需要配置一個模型")
        
        # 驗證每個模型配置
        for name, model_config in self.models.items():
            if not model_config.api_key:
                raise ValueError(f"模型 {name} 缺少API密鑰")
            if not model_config.model:
                raise ValueError(f"模型 {name} 缺少模型名稱")
        
        # 驗證日誌級別
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.level not in valid_log_levels:
            raise ValueError(f"無效的日誌級別: {self.logging.level}")
        
        return True


# 默認配置實例
default_config = StandardConfig()

# 全局配置實例
_global_config: Optional[StandardConfig] = None


def get_config() -> StandardConfig:
    """獲取全局配置"""
    global _global_config
    if _global_config is None:
        _global_config = StandardConfig.from_env()
    return _global_config


def set_config(config: StandardConfig):
    """設置全局配置"""
    global _global_config
    config.validate()
    _global_config = config


def load_config_from_file(config_path: str):
    """從文件加載全局配置"""
    config = StandardConfig.from_file(config_path)
    set_config(config)


def reset_config():
    """重置為默認配置"""
    global _global_config
    _global_config = None