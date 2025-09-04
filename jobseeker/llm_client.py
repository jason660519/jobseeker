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
            
            # 初始化客戶端
            self.client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
            
            self.logger.info(f"OpenAI客戶端初始化成功: {self.config.model_name}")
            
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
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "response_format": kwargs.get("response_format", {"type": "json_object"})
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


class MockLLMClient(BaseLLMClient):
    """模擬LLM客戶端（用於測試和演示）"""
    
    def __init__(self, config: LLMConfig):
        """初始化模擬客戶端"""
        super().__init__(config)
        self.logger.info("模擬LLM客戶端初始化成功")
    
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """模擬LLM調用"""
        start_time = time.time()
        
        # 模擬處理延遲
        time.sleep(0.1)
        
        # 提取用戶查詢
        user_query = ""
        for msg in messages:
            if msg["role"] == "user":
                user_query = msg["content"]
                break
        
        # 生成模擬響應
        mock_response = self._generate_mock_response(user_query)
        
        response_time = time.time() - start_time
        
        return LLMResponse(
            content=json.dumps(mock_response, ensure_ascii=False),
            usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            model=self.config.model_name,
            provider=self.config.provider,
            response_time=response_time,
            success=True
        )
    
    async def acall(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """異步模擬LLM調用"""
        await asyncio.sleep(0.1)  # 模擬異步延遲
        return self.call(messages, **kwargs)
    
    def _generate_mock_response(self, query: str) -> Dict[str, Any]:
        """生成模擬響應"""
        query_lower = query.lower()
        
        # 檢查是否為非求職相關查詢
        non_job_keywords = ['天氣', '電影', '音樂', '食譜', '烹飪', '遊戲', '娛樂']
        if any(keyword in query_lower for keyword in non_job_keywords):
            return {
                "is_job_related": False,
                "intent_type": "non_job_related",
                "confidence": 0.9,
                "reasoning": "查詢內容與求職無關，涉及日常生活話題",
                "structured_intent": None,
                "search_suggestions": [],
                "response_message": "抱歉，我是AI助手，僅能協助您處理求職相關問題。您可以嘗試搜索：'軟體工程師 台北'、'產品經理 薪資'等求職相關內容。"
            }
        
        # 模擬求職相關分析
        job_titles = []
        skills = []
        locations = []
        soft_preferences = []
        
        # 智能提取職位
        if any(title in query_lower for title in ['工程師', 'engineer', '開發', 'developer']):
            if 'frontend' in query_lower or '前端' in query_lower:
                job_titles.append('前端工程師')
                skills.extend(['JavaScript', 'React', 'Vue'])
            elif 'backend' in query_lower or '後端' in query_lower:
                job_titles.append('後端工程師')
                skills.extend(['Python', 'Java', 'Node.js'])
            elif 'ai' in query_lower or '人工智慧' in query_lower or '機器學習' in query_lower:
                job_titles.append('AI工程師')
                skills.extend(['Python', 'TensorFlow', 'PyTorch', 'Machine Learning'])
            else:
                job_titles.append('軟體工程師')
        
        if '產品經理' in query or 'product manager' in query_lower:
            job_titles.append('產品經理')
            skills.extend(['產品規劃', '用戶研究', '數據分析'])
        
        if '資料科學' in query or 'data scientist' in query_lower:
            job_titles.append('資料科學家')
            skills.extend(['Python', 'R', 'SQL', '機器學習', '統計分析'])
        
        # 智能提取地點
        location_keywords = {
            '台北': '台北市',
            '新北': '新北市',
            '台中': '台中市',
            '高雄': '高雄市',
            '新竹': '新竹市',
            'sydney': '雪梨',
            'melbourne': '墨爾本',
            'brisbane': '布里斯本',
            'singapore': '新加坡'
        }
        
        for keyword, location in location_keywords.items():
            if keyword in query_lower:
                locations.append(location)
        
        if '遠程' in query or 'remote' in query_lower or '在家工作' in query_lower:
            locations.append('遠程工作')
        
        # 智能提取軟性偏好
        if '不加班' in query or '不想加班' in query or 'work life balance' in query_lower:
            soft_preferences.extend(['工作生活平衡', '正常工時', '不加班'])
        
        if '團隊氛圍' in query or '文化' in query or 'culture' in query_lower:
            soft_preferences.extend(['團隊氛圍好', '企業文化佳'])
        
        if '學習' in query or '成長' in query or 'learning' in query_lower:
            soft_preferences.extend(['學習機會多', '職業發展'])
        
        if '彈性' in query or 'flexible' in query_lower:
            soft_preferences.extend(['彈性工時', '彈性工作'])
        
        # 提取薪資信息
        import re
        salary_patterns = [
            r'(\d+)[-到~]?(\d+)?[萬k萬元]',
            r'薪水.*?(\d+)',
            r'salary.*?(\d+)',
            r'(\d+)k'
        ]
        
        salary_range = None
        for pattern in salary_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if match.group(2):
                    salary_range = f"{match.group(1)}-{match.group(2)}萬"
                else:
                    salary_range = f"{match.group(1)}萬以上"
                break
        
        # 提取工作模式
        work_mode = None
        if '遠程' in query or 'remote' in query_lower:
            work_mode = "遠程"
        elif '混合' in query or 'hybrid' in query_lower:
            work_mode = "混合"
        elif '線下' in query or 'onsite' in query_lower:
            work_mode = "線下"
        
        # 提取經驗要求
        experience_level = None
        exp_patterns = {
            r'(\d+)[-到~]?(\d+)?年': lambda m: f"{m.group(1)}-{m.group(2) or m.group(1)}年" if m.group(2) else f"{m.group(1)}年以上",
            r'新手|junior|初級': "1-2年",
            r'資深|senior|高級': "5年以上",
            r'主管|manager|lead': "主管級",
            r'實習|intern': "實習生"
        }
        
        for pattern, result in exp_patterns.items():
            if callable(result):
                match = re.search(pattern, query_lower)
                if match:
                    experience_level = result(match)
                    break
            else:
                if re.search(pattern, query_lower):
                    experience_level = result
                    break
        
        # 生成搜索建議
        search_suggestions = []
        if job_titles and locations:
            search_suggestions.append(f"{job_titles[0]} {locations[0]}")
        if job_titles and skills:
            search_suggestions.append(f"{job_titles[0]} {' '.join(skills[:2])}")
        if job_titles and salary_range:
            search_suggestions.append(f"{job_titles[0]} {salary_range}")
        
        # 如果沒有明確的求職意圖，提供通用建議
        if not job_titles and not skills:
            search_suggestions = [
                "軟體工程師 台北",
                "產品經理 遠程工作",
                "資料科學家 新竹"
            ]
        
        return {
            "is_job_related": bool(job_titles or skills or locations or '工作' in query or 'job' in query_lower),
            "intent_type": "job_search",
            "confidence": 0.8 if job_titles else 0.6,
            "reasoning": "基於關鍵詞和語義分析，識別出求職相關意圖並提取結構化信息",
            "structured_intent": {
                "job_titles": job_titles,
                "skills": skills,
                "locations": locations,
                "salary_range": salary_range,
                "work_mode": work_mode,
                "company_size": None,
                "industry": None,
                "experience_level": experience_level,
                "soft_preferences": soft_preferences,
                "urgency": None
            },
            "search_suggestions": search_suggestions,
            "response_message": "已為您分析查詢意圖，正在搜索相關職位..."
        }


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
        """
        if config.provider in [LLMProvider.OPENAI, LLMProvider.AZURE_OPENAI]:
            return OpenAIClient(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(config)
        elif config.provider == LLMProvider.GOOGLE:
            return GoogleClient(config)
        elif config.provider == LLMProvider.DEEPSEEKER:
            return DeepseekerClient(config)
        elif config.provider == LLMProvider.MOCK:
            return MockLLMClient(config)
        else:
            # 默認返回Mock客戶端
            return MockLLMClient(config)


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