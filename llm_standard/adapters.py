"""LLM提供商適配器模組"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import openai
import anthropic
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic

from .exceptions import (
    LLMStandardError,
    InvalidInputError,
    TokenLimitExceededError,
    TimeoutError,
    ModelUnavailableError,
    RateLimitExceededError,
    ContentFilteredError,
    ParsingError
)
from .validators import SchemaValidator


class BaseLLMAdapter(ABC):
    """LLM適配器基礎類"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.schema_validator = SchemaValidator()
        self.provider_name = self.__class__.__name__.replace('Adapter', '').lower()
        
        # 通用配置
        self.timeout = kwargs.get('timeout', 30)
        self.max_retries = kwargs.get('max_retries', 3)
        self.base_delay = kwargs.get('base_delay', 1.0)
        
    @abstractmethod
    def format_instruction(self, standard_instruction: Dict[str, Any]) -> str:
        """將標準指令格式轉換為提供商特定格式"""
        pass
    
    @abstractmethod
    def parse_response(self, raw_response: Any, request_id: str, start_time: float) -> Dict[str, Any]:
        """將提供商響應解析為標準格式"""
        pass
    
    @abstractmethod
    def _make_api_call(self, formatted_instruction: str, **kwargs) -> Any:
        """執行實際的API調用"""
        pass
    
    def execute(self, instruction: Dict[str, Any], input_text: str, **kwargs) -> Dict[str, Any]:
        """
        執行指令並返回標準格式響應
        
        Args:
            instruction: 標準指令格式
            input_text: 輸入文本
            **kwargs: 額外參數
            
        Returns:
            Dict[str, Any]: 標準格式響應
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 格式化指令
            formatted_instruction = self.format_instruction(instruction)
            
            # 添加輸入文本
            full_prompt = f"{formatted_instruction}\n\nInput Content: {input_text}"
            
            # 執行API調用
            raw_response = self._make_api_call(full_prompt, **kwargs)
            
            # 解析響應
            standard_response = self.parse_response(raw_response, request_id, start_time)
            
            # 驗證輸出Schema（如果指定）
            if 'output_schema' in instruction:
                self._validate_output_schema(
                    standard_response.get('data', {}),
                    instruction['output_schema']
                )
            
            return standard_response
            
        except Exception as e:
            return self._create_error_response(e, request_id, start_time)
    
    def _validate_output_schema(self, data: Any, schema: Dict[str, Any]) -> None:
        """驗證輸出是否符合Schema"""
        try:
            self.schema_validator.validate_strict(data, schema)
        except Exception as e:
            raise ParsingError(f"輸出不符合指定Schema: {str(e)}")
    
    def _create_error_response(self, error: Exception, request_id: str, start_time: float) -> Dict[str, Any]:
        """創建錯誤響應"""
        processing_time = time.time() - start_time
        
        if isinstance(error, LLMStandardError):
            error_info = error.to_dict()
        else:
            error_info = {
                "code": "E999",
                "message": str(error),
                "details": type(error).__name__,
                "severity": "error"
            }
        
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_info": {
                "provider": self.provider_name,
                "model": self.model,
                "version": "unknown"
            },
            "request_id": request_id,
            "data": {},
            "metadata": {
                "processing_time": processing_time,
                "token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "confidence_score": 0.0
            },
            "errors": [error_info],
            "warnings": []
        }
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """從文本中提取JSON"""
        try:
            # 嘗試直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            # 嘗試提取JSON代碼塊
            import re
            json_pattern = r'```(?:json)?\s*({.*?})\s*```'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
            
            # 嘗試提取大括號內容
            brace_pattern = r'{.*}'
            matches = re.findall(brace_pattern, text, re.DOTALL)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
            
            raise ParsingError(f"無法從響應中提取有效JSON: {text[:200]}...")


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI適配器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(api_key=api_key)
        self.provider_name = "openai"
    
    def format_instruction(self, standard_instruction: Dict[str, Any]) -> str:
        """格式化OpenAI指令"""
        task = standard_instruction.get('task', {})
        description = task.get('description', '')
        context = task.get('context', '')
        constraints = task.get('constraints', [])
        
        prompt = f"Task Description: {description}\n"
        
        if context:
            prompt += f"Context: {context}\n"
        
        if constraints:
            prompt += f"Constraints: {', '.join(constraints)}\n"
        
        # 添加輸出格式要求
        if 'output_schema' in standard_instruction:
            schema_str = json.dumps(standard_instruction['output_schema'], ensure_ascii=False, indent=2)
            prompt += f"\nPlease output results according to the following JSON Schema format:\n{schema_str}\n"
            prompt += "\nPlease ensure the output is valid JSON format without any additional text explanations."
        
        return prompt
    
    def _make_api_call(self, formatted_instruction: str, **kwargs) -> Any:
        """執行OpenAI API調用"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional AI assistant. Please strictly follow the user's required format for output."},
                    {"role": "user", "content": formatted_instruction}
                ],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000),
                timeout=self.timeout
            )
            return response
        except openai.RateLimitError as e:
            raise RateLimitExceededError(f"OpenAI速率限制: {str(e)}")
        except openai.APITimeoutError as e:
            raise TimeoutError(f"OpenAI請求超時: {str(e)}")
        except openai.APIError as e:
            raise ModelUnavailableError(f"OpenAI API錯誤: {str(e)}")
    
    def parse_response(self, raw_response: Any, request_id: str, start_time: float) -> Dict[str, Any]:
        """解析OpenAI響應"""
        processing_time = time.time() - start_time
        
        try:
            content = raw_response.choices[0].message.content
            usage = raw_response.usage
            
            # 提取JSON數據
            data = self._extract_json_from_text(content)
            
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_info": {
                    "provider": self.provider_name,
                    "model": raw_response.model,
                    "version": "unknown"
                },
                "request_id": request_id,
                "data": data,
                "metadata": {
                    "processing_time": processing_time,
                    "token_usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    },
                    "confidence_score": 0.9  # OpenAI沒有提供置信度分數
                },
                "errors": [],
                "warnings": []
            }
        except Exception as e:
            raise ParsingError(f"解析OpenAI響應失敗: {str(e)}")


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic適配器"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = Anthropic(api_key=api_key)
        self.provider_name = "anthropic"
    
    def format_instruction(self, standard_instruction: Dict[str, Any]) -> str:
        """格式化Anthropic指令"""
        task = standard_instruction.get('task', {})
        description = task.get('description', '')
        context = task.get('context', '')
        constraints = task.get('constraints', [])
        
        prompt = f"<task>\n{description}\n</task>\n"
        
        if context:
            prompt += f"<context>\n{context}\n</context>\n"
        
        if constraints:
            prompt += f"<constraints>\n{', '.join(constraints)}\n</constraints>\n"
        
        # 添加輸出格式要求
        if 'output_schema' in standard_instruction:
            schema_str = json.dumps(standard_instruction['output_schema'], ensure_ascii=False, indent=2)
            prompt += f"\n<output_format>\nPlease output results according to the following JSON Schema format:\n{schema_str}\n</output_format>\n"
            prompt += "\nPlease ensure the output is valid JSON format without any additional text explanations."
        
        return prompt
    
    def _make_api_call(self, formatted_instruction: str, **kwargs) -> Any:
        """執行Anthropic API調用"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 2000),
                temperature=kwargs.get('temperature', 0.1),
                messages=[
                    {"role": "user", "content": formatted_instruction}
                ],
                timeout=self.timeout
            )
            return response
        except anthropic.RateLimitError as e:
            raise RateLimitExceededError(f"Anthropic速率限制: {str(e)}")
        except anthropic.APITimeoutError as e:
            raise TimeoutError(f"Anthropic請求超時: {str(e)}")
        except anthropic.APIError as e:
            raise ModelUnavailableError(f"Anthropic API錯誤: {str(e)}")
    
    def parse_response(self, raw_response: Any, request_id: str, start_time: float) -> Dict[str, Any]:
        """解析Anthropic響應"""
        processing_time = time.time() - start_time
        
        try:
            content = raw_response.content[0].text
            usage = raw_response.usage
            
            # 提取JSON數據
            data = self._extract_json_from_text(content)
            
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_info": {
                    "provider": self.provider_name,
                    "model": raw_response.model,
                    "version": "unknown"
                },
                "request_id": request_id,
                "data": data,
                "metadata": {
                    "processing_time": processing_time,
                    "token_usage": {
                        "prompt_tokens": usage.input_tokens,
                        "completion_tokens": usage.output_tokens,
                        "total_tokens": usage.input_tokens + usage.output_tokens
                    },
                    "confidence_score": 0.9  # Anthropic沒有提供置信度分數
                },
                "errors": [],
                "warnings": []
            }
        except Exception as e:
            raise ParsingError(f"解析Anthropic響應失敗: {str(e)}")


class GoogleAdapter(BaseLLMAdapter):
    """Google適配器"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        super().__init__(api_key, model, **kwargs)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        self.provider_name = "google"
    
    def format_instruction(self, standard_instruction: Dict[str, Any]) -> str:
        """格式化Google指令"""
        task = standard_instruction.get('task', {})
        description = task.get('description', '')
        context = task.get('context', '')
        constraints = task.get('constraints', [])
        
        prompt = f"Task: {description}\n"
        
        if context:
            prompt += f"Background: {context}\n"
        
        if constraints:
            prompt += f"Requirements: {', '.join(constraints)}\n"
        
        # 添加輸出格式要求
        if 'output_schema' in standard_instruction:
            schema_str = json.dumps(standard_instruction['output_schema'], ensure_ascii=False, indent=2)
            prompt += f"\nOutput Format (JSON Schema):\n{schema_str}\n"
            prompt += "\nPlease strictly follow the above JSON format for output, without any additional explanations."
        
        return prompt
    
    def _make_api_call(self, formatted_instruction: str, **kwargs) -> Any:
        """執行Google API調用"""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', 0.1),
                max_output_tokens=kwargs.get('max_tokens', 2000)
            )
            
            response = self.client.generate_content(
                formatted_instruction,
                generation_config=generation_config
            )
            return response
        except Exception as e:
            if "quota" in str(e).lower():
                raise RateLimitExceededError(f"Google配額限制: {str(e)}")
            elif "timeout" in str(e).lower():
                raise TimeoutError(f"Google請求超時: {str(e)}")
            else:
                raise ModelUnavailableError(f"Google API錯誤: {str(e)}")
    
    def parse_response(self, raw_response: Any, request_id: str, start_time: float) -> Dict[str, Any]:
        """解析Google響應"""
        processing_time = time.time() - start_time
        
        try:
            content = raw_response.text
            
            # 提取JSON數據
            data = self._extract_json_from_text(content)
            
            # Google API的token使用信息可能不完整
            token_usage = {
                "prompt_tokens": getattr(raw_response.usage_metadata, 'prompt_token_count', 0),
                "completion_tokens": getattr(raw_response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(raw_response.usage_metadata, 'total_token_count', 0)
            }
            
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_info": {
                    "provider": self.provider_name,
                    "model": self.model,
                    "version": "unknown"
                },
                "request_id": request_id,
                "data": data,
                "metadata": {
                    "processing_time": processing_time,
                    "token_usage": token_usage,
                    "confidence_score": 0.85  # Google沒有提供置信度分數
                },
                "errors": [],
                "warnings": []
            }
        except Exception as e:
            raise ParsingError(f"解析Google響應失敗: {str(e)}")


class DeepSeekAdapter(BaseLLMAdapter):
    """DeepSeek適配器（使用OpenAI兼容接口）"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.provider_name = "deepseek"
    
    def format_instruction(self, standard_instruction: Dict[str, Any]) -> str:
        """格式化DeepSeek指令"""
        task = standard_instruction.get('task', {})
        description = task.get('description', '')
        context = task.get('context', '')
        constraints = task.get('constraints', [])
        
        prompt = f"Task: {description}\n"
        
        if context:
            prompt += f"Context: {context}\n"
        
        if constraints:
            prompt += f"Constraints: {', '.join(constraints)}\n"
        
        # 添加輸出格式要求
        if 'output_schema' in standard_instruction:
            schema_str = json.dumps(standard_instruction['output_schema'], ensure_ascii=False, indent=2)
            prompt += f"\nOutput Format Requirements (JSON Schema):\n{schema_str}\n"
            prompt += "\nPlease strictly follow JSON format for output, without adding any explanatory text."
        
        return prompt
    
    def _make_api_call(self, formatted_instruction: str, **kwargs) -> Any:
        """執行DeepSeek API調用"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一個專業的AI助手，請嚴格按照用戶要求的JSON格式輸出結果。"},
                    {"role": "user", "content": formatted_instruction}
                ],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000),
                timeout=self.timeout
            )
            return response
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise RateLimitExceededError(f"DeepSeek速率限制: {str(e)}")
            elif "timeout" in error_str:
                raise TimeoutError(f"DeepSeek請求超時: {str(e)}")
            else:
                raise ModelUnavailableError(f"DeepSeek API錯誤: {str(e)}")
    
    def parse_response(self, raw_response: Any, request_id: str, start_time: float) -> Dict[str, Any]:
        """解析DeepSeek響應"""
        processing_time = time.time() - start_time
        
        try:
            content = raw_response.choices[0].message.content
            usage = raw_response.usage
            
            # 提取JSON數據
            data = self._extract_json_from_text(content)
            
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_info": {
                    "provider": self.provider_name,
                    "model": raw_response.model,
                    "version": "unknown"
                },
                "request_id": request_id,
                "data": data,
                "metadata": {
                    "processing_time": processing_time,
                    "token_usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    },
                    "confidence_score": 0.88  # DeepSeek沒有提供置信度分數
                },
                "errors": [],
                "warnings": []
            }
        except Exception as e:
            raise ParsingError(f"解析DeepSeek響應失敗: {str(e)}")


# 適配器工廠
ADAPTER_MAP = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "google": GoogleAdapter,
    "deepseek": DeepSeekAdapter
}


def create_adapter(provider: str, api_key: str, model: str, **kwargs) -> BaseLLMAdapter:
    """創建適配器實例"""
    if provider not in ADAPTER_MAP:
        raise InvalidInputError(f"不支持的提供商: {provider}")
    
    adapter_class = ADAPTER_MAP[provider]
    return adapter_class(api_key, model, **kwargs)