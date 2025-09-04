"""統一LLM客戶端"""

import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone

from .adapters import create_adapter, BaseLLMAdapter
from .validators import InstructionValidator, ResponseValidator
from .exceptions import (
    LLMStandardError,
    InvalidInputError,
    TimeoutError,
    ModelUnavailableError
)


class StandardLLMClient:
    """統一LLM客戶端"""
    
    def __init__(self, 
                 provider: str,
                 api_key: str,
                 model: str,
                 **kwargs):
        """
        初始化統一LLM客戶端
        
        Args:
            provider: LLM提供商 (openai, anthropic, google, deepseek)
            api_key: API密鑰
            model: 模型名稱
            **kwargs: 額外配置參數
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        
        # 創建適配器
        self.adapter = create_adapter(provider, api_key, model, **kwargs)
        
        # 創建驗證器
        self.instruction_validator = InstructionValidator()
        self.response_validator = ResponseValidator()
        
        # 配置
        self.validate_instructions = kwargs.get('validate_instructions', True)
        self.validate_responses = kwargs.get('validate_responses', True)
        self.auto_retry = kwargs.get('auto_retry', True)
        self.max_retries = kwargs.get('max_retries', 3)
        
    def execute(self, 
                instruction: Dict[str, Any], 
                input_text: str,
                **kwargs) -> Dict[str, Any]:
        """
        執行指令
        
        Args:
            instruction: 標準指令格式
            input_text: 輸入文本
            **kwargs: 額外參數
            
        Returns:
            Dict[str, Any]: 標準格式響應
        """
        # 驗證指令格式
        if self.validate_instructions:
            try:
                self.instruction_validator.validate_instruction_strict(instruction)
            except Exception as e:
                raise InvalidInputError(f"指令格式驗證失敗: {str(e)}")
        
        # 執行指令（帶重試機制）
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.adapter.execute(instruction, input_text, **kwargs)
                
                # 驗證響應格式
                if self.validate_responses:
                    try:
                        self.response_validator.validate_response_strict(response)
                    except Exception as e:
                        # 響應格式錯誤不重試，直接返回
                        response['warnings'] = response.get('warnings', [])
                        response['warnings'].append({
                            "code": "W001",
                            "message": f"響應格式驗證警告: {str(e)}"
                        })
                
                return response
                
            except (TimeoutError, ModelUnavailableError) as e:
                last_error = e
                if attempt < self.max_retries and self.auto_retry:
                    # 指數退避
                    delay = (2 ** attempt) * self.adapter.base_delay
                    time.sleep(min(delay, 60))  # 最大延遲60秒
                    continue
                else:
                    break
            except Exception as e:
                # 其他錯誤不重試
                last_error = e
                break
        
        # 如果所有重試都失敗，拋出最後一個錯誤
        if last_error:
            raise last_error
    
    def execute_batch(self, 
                      instructions: List[Dict[str, Any]], 
                      input_texts: List[str],
                      **kwargs) -> List[Dict[str, Any]]:
        """
        批量執行指令
        
        Args:
            instructions: 指令列表
            input_texts: 輸入文本列表
            **kwargs: 額外參數
            
        Returns:
            List[Dict[str, Any]]: 響應列表
        """
        if len(instructions) != len(input_texts):
            raise InvalidInputError("指令數量與輸入文本數量不匹配")
        
        results = []
        for instruction, input_text in zip(instructions, input_texts):
            try:
                result = self.execute(instruction, input_text, **kwargs)
                results.append(result)
            except Exception as e:
                # 批量執行中的錯誤不中斷整個流程
                error_response = self.adapter._create_error_response(
                    e, f"batch_{len(results)}", time.time()
                )
                results.append(error_response)
        
        return results
    
    def create_instruction(self,
                          instruction_type: str,
                          description: str,
                          output_schema: Optional[Dict[str, Any]] = None,
                          context: Optional[str] = None,
                          constraints: Optional[List[str]] = None,
                          examples: Optional[List[Dict[str, Any]]] = None,
                          priority: str = "medium",
                          timeout: int = 30,
                          retry_count: int = 3) -> Dict[str, Any]:
        """
        創建標準指令
        
        Args:
            instruction_type: 指令類型
            description: 任務描述
            output_schema: 輸出Schema（可選）
            context: 上下文（可選）
            constraints: 約束條件（可選）
            examples: 示例（可選）
            priority: 優先級
            timeout: 超時時間
            retry_count: 重試次數
            
        Returns:
            Dict[str, Any]: 標準指令格式
        """
        instruction = {
            "instruction_type": instruction_type,
            "version": "1.0",
            "task": {
                "description": description
            },
            "metadata": {
                "priority": priority,
                "timeout": timeout,
                "retry_count": retry_count
            }
        }
        
        if context:
            instruction["task"]["context"] = context
        
        if constraints:
            instruction["task"]["constraints"] = constraints
        
        if output_schema:
            instruction["output_schema"] = output_schema
        
        if examples:
            instruction["examples"] = examples
        
        return instruction
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        
        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        try:
            # 創建簡單的測試指令
            test_instruction = self.create_instruction(
                instruction_type="text_generation",
                description="回復'OK'",
                timeout=10
            )
            
            response = self.execute(test_instruction, "健康檢查")
            
            return {
                "status": "healthy",
                "provider": self.provider,
                "model": self.model,
                "response_time": response["metadata"]["processing_time"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider,
                "model": self.model,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        獲取支持的功能列表
        
        Returns:
            Dict[str, bool]: 功能支持情況
        """
        # 基於提供商返回功能支持矩陣
        feature_matrix = {
            "openai": {
                "structured_output": True,
                "json_schema_validation": True,
                "function_calling": True,
                "streaming": True,
                "multimodal": True,
                "batch_processing": True
            },
            "anthropic": {
                "structured_output": True,
                "json_schema_validation": True,
                "function_calling": True,
                "streaming": True,
                "multimodal": True,
                "batch_processing": True
            },
            "google": {
                "structured_output": True,
                "json_schema_validation": False,  # 部分支持
                "function_calling": True,
                "streaming": True,
                "multimodal": True,
                "batch_processing": True
            },
            "deepseek": {
                "structured_output": True,
                "json_schema_validation": True,
                "function_calling": False,
                "streaming": True,
                "multimodal": False,
                "batch_processing": True
            }
        }
        
        return feature_matrix.get(self.provider, {})
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        獲取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "supported_features": self.get_supported_features(),
            "max_tokens": self._get_max_tokens(),
            "supports_system_message": self._supports_system_message()
        }
    
    def _get_max_tokens(self) -> int:
        """獲取模型最大token數"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "claude-3-haiku-20240307": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-opus-20240229": 200000,
            "gemini-pro": 32768,
            "gemini-1.5-pro": 1048576,
            "deepseek-chat": 32768
        }
        return token_limits.get(self.model, 4096)
    
    def _supports_system_message(self) -> bool:
        """檢查是否支持系統消息"""
        return self.provider in ["openai", "anthropic", "deepseek"]


class LLMClientPool:
    """LLM客戶端池，支持負載均衡和故障轉移"""
    
    def __init__(self, clients: List[StandardLLMClient]):
        """
        初始化客戶端池
        
        Args:
            clients: 客戶端列表
        """
        self.clients = clients
        self.current_index = 0
        self.failed_clients = set()
    
    def execute(self, instruction: Dict[str, Any], input_text: str, **kwargs) -> Dict[str, Any]:
        """
        使用負載均衡執行指令
        
        Args:
            instruction: 標準指令格式
            input_text: 輸入文本
            **kwargs: 額外參數
            
        Returns:
            Dict[str, Any]: 標準格式響應
        """
        available_clients = [i for i in range(len(self.clients)) if i not in self.failed_clients]
        
        if not available_clients:
            # 重置失敗客戶端列表
            self.failed_clients.clear()
            available_clients = list(range(len(self.clients)))
        
        # 輪詢選擇客戶端
        for _ in range(len(available_clients)):
            client_index = available_clients[self.current_index % len(available_clients)]
            client = self.clients[client_index]
            
            try:
                response = client.execute(instruction, input_text, **kwargs)
                self.current_index = (self.current_index + 1) % len(available_clients)
                return response
            except Exception as e:
                # 標記客戶端為失敗
                self.failed_clients.add(client_index)
                self.current_index = (self.current_index + 1) % len(available_clients)
                
                # 如果是最後一個可用客戶端，拋出錯誤
                if len(self.failed_clients) >= len(self.clients):
                    raise e
        
        raise ModelUnavailableError("所有客戶端都不可用")
    
    def health_check_all(self) -> Dict[str, Any]:
        """
        檢查所有客戶端的健康狀態
        
        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        results = {}
        for i, client in enumerate(self.clients):
            try:
                result = client.health_check()
                results[f"client_{i}_{client.provider}_{client.model}"] = result
            except Exception as e:
                results[f"client_{i}_{client.provider}_{client.model}"] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        return results