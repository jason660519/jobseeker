"""LLM標準庫測試套件"""

import json
import pytest
import time
from unittest.mock import Mock, patch
from llm_standard import StandardLLMClient
from llm_standard.client import LLMClientPool
from llm_standard.validators import SchemaValidator, ResponseValidator, InstructionValidator
from llm_standard.adapters import OpenAIAdapter, AnthropicAdapter, GoogleAdapter, DeepSeekAdapter
from llm_standard.exceptions import (
    InvalidInputError, SchemaValidationError, TokenLimitExceededError,
    ProviderError, TimeoutError, RateLimitError
)


class TestSchemaValidator:
    """Schema驗證器測試"""
    
    def setup_method(self):
        """測試前設置"""
        self.validator = SchemaValidator()
    
    def test_basic_validation(self):
        """基本驗證測試"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        # 有效數據
        valid_data = {"name": "張三", "age": 25}
        assert self.validator.validate(valid_data, schema) == True
        
        # 無效數據 - 缺少必需字段
        invalid_data = {"age": 25}
        with pytest.raises(SchemaValidationError):
            self.validator.validate(invalid_data, schema)
    
    def test_custom_formats(self):
        """自定義格式測試"""
        schema = {
            "type": "object",
            "properties": {
                "datetime": {"type": "string", "format": "datetime-iso8601"},
                "phone": {"type": "string", "format": "phone-number"},
                "name": {"type": "string", "format": "chinese-name"}
            }
        }
        
        # 有效格式
        valid_data = {
            "datetime": "2024-01-15T10:30:00Z",
            "phone": "13812345678",
            "name": "李小明"
        }
        assert self.validator.validate(valid_data, schema) == True
        
        # 無效格式
        invalid_data = {
            "datetime": "invalid-date",
            "phone": "invalid-phone",
            "name": "123"
        }
        with pytest.raises(SchemaValidationError):
            self.validator.validate(invalid_data, schema)


class TestResponseValidator:
    """響應驗證器測試"""
    
    def setup_method(self):
        """測試前設置"""
        self.validator = ResponseValidator()
    
    def test_valid_response(self):
        """有效響應測試"""
        response = {
            "status": "success",
            "data": {"result": "test"},
            "metadata": {
                "model_info": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "version": "1.0"
                },
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                },
                "processing_time": 1.5,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
        assert self.validator.validate(response) == True
    
    def test_error_response(self):
        """錯誤響應測試"""
        response = {
            "status": "error",
            "errors": [
                {
                    "code": "INVALID_INPUT",
                    "message": "輸入無效",
                    "details": {"field": "input"}
                }
            ],
            "metadata": {
                "model_info": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "version": "1.0"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
        assert self.validator.validate(response) == True


class TestInstructionValidator:
    """指令驗證器測試"""
    
    def setup_method(self):
        """測試前設置"""
        self.validator = InstructionValidator()
    
    def test_valid_instruction(self):
        """有效指令測試"""
        instruction = {
            "instruction_type": "structured_output",
            "version": "1.0",
            "task": {
                "description": "測試任務"
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                },
                "required": ["result"]
            }
        }
        
        assert self.validator.validate(instruction) == True
    
    def test_invalid_instruction(self):
        """無效指令測試"""
        # 缺少必需字段
        invalid_instruction = {
            "instruction_type": "structured_output",
            "version": "1.0"
        }
        
        with pytest.raises(SchemaValidationError):
            self.validator.validate(invalid_instruction)


class TestAdapters:
    """適配器測試"""
    
    def test_openai_adapter(self):
        """OpenAI適配器測試"""
        adapter = OpenAIAdapter()
        
        instruction = {
            "instruction_type": "structured_output",
            "version": "1.0",
            "task": {
                "description": "生成用戶信息"
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        }
        
        user_input = "創建一個25歲的用戶張三"
        
        # 測試指令轉換
        converted = adapter.convert_instruction(instruction, user_input)
        
        assert "messages" in converted
        assert len(converted["messages"]) > 0
        assert "response_format" in converted
        assert converted["response_format"]["type"] == "json_object"
    
    def test_anthropic_adapter(self):
        """Anthropic適配器測試"""
        adapter = AnthropicAdapter()
        
        instruction = {
            "instruction_type": "text_analysis",
            "version": "1.0",
            "task": {
                "description": "分析文本情感"
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        }
        
        user_input = "這個產品很棒！"
        
        # 測試指令轉換
        converted = adapter.convert_instruction(instruction, user_input)
        
        assert "messages" in converted
        assert len(converted["messages"]) > 0
        assert "max_tokens" in converted


class TestStandardLLMClient:
    """標準LLM客戶端測試"""
    
    def setup_method(self):
        """測試前設置"""
        self.client = StandardLLMClient(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
    
    @patch('llm_standard.adapters.OpenAIAdapter.call_api')
    def test_execute_success(self, mock_call_api):
        """成功執行測試"""
        # 模擬API響應
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"name": "張三", "age": 25}'
                }
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_call_api.return_value = mock_response
        
        instruction = {
            "instruction_type": "structured_output",
            "version": "1.0",
            "task": {
                "description": "生成用戶信息"
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"]
            }
        }
        
        user_input = "創建一個25歲的用戶張三"
        
        response = self.client.execute(instruction, user_input)
        
        assert response["status"] == "success"
        assert response["data"]["name"] == "張三"
        assert response["data"]["age"] == 25
        assert "metadata" in response
    
    def test_create_instruction(self):
        """創建指令測試"""
        instruction = self.client.create_instruction(
            instruction_type="text_generation",
            description="生成產品描述",
            output_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                }
            },
            constraints=["max_length: 200", "language: zh-CN"]
        )
        
        assert instruction["instruction_type"] == "text_generation"
        assert instruction["version"] == "1.0"
        assert "task" in instruction
        assert "output_schema" in instruction
        assert len(instruction["task"]["constraints"]) == 2
    
    @patch('llm_standard.adapters.OpenAIAdapter.call_api')
    def test_batch_execute(self, mock_call_api):
        """批量執行測試"""
        # 模擬API響應
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"sentiment": "positive", "confidence": 0.9}'
                }
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75
            }
        }
        mock_call_api.return_value = mock_response
        
        instruction = {
            "instruction_type": "text_analysis",
            "version": "1.0",
            "task": {
                "description": "分析文本情感"
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        }
        
        inputs = ["這個產品很棒！", "服務一般般。", "非常失望。"]
        
        responses = self.client.batch_execute(instruction, inputs)
        
        assert len(responses) == 3
        for response in responses:
            assert response["status"] == "success"
            assert "sentiment" in response["data"]
            assert "confidence" in response["data"]


class TestLLMClientPool:
    """LLM客戶端池測試"""
    
    def setup_method(self):
        """測試前設置"""
        self.clients = [
            StandardLLMClient(provider="openai", api_key="test-key-1", model="gpt-4"),
            StandardLLMClient(provider="anthropic", api_key="test-key-2", model="claude-3-haiku"),
            StandardLLMClient(provider="deepseek", api_key="test-key-3", model="deepseek-chat")
        ]
        self.pool = LLMClientPool(self.clients)
    
    def test_pool_initialization(self):
        """池初始化測試"""
        assert len(self.pool.clients) == 3
        assert self.pool.current_index == 0
        assert self.pool.strategy == "round_robin"
    
    def test_get_next_client(self):
        """獲取下一個客戶端測試"""
        client1 = self.pool._get_next_client()
        client2 = self.pool._get_next_client()
        client3 = self.pool._get_next_client()
        client4 = self.pool._get_next_client()  # 應該回到第一個
        
        assert client1 == self.clients[0]
        assert client2 == self.clients[1]
        assert client3 == self.clients[2]
        assert client4 == self.clients[0]
    
    @patch('llm_standard.client.StandardLLMClient.execute')
    def test_execute_with_fallback(self, mock_execute):
        """故障轉移執行測試"""
        # 第一個客戶端失敗，第二個成功
        mock_execute.side_effect = [
            Exception("API錯誤"),
            {
                "status": "success",
                "data": {"result": "test"},
                "metadata": {
                    "model_info": {"provider": "anthropic", "model": "claude-3-haiku"},
                    "token_usage": {"total_tokens": 100},
                    "processing_time": 1.0,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        ]
        
        instruction = {
            "instruction_type": "test",
            "version": "1.0",
            "task": {"description": "測試任務"},
            "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}}
        }
        
        response = self.pool.execute(instruction, "test input")
        
        assert response["status"] == "success"
        assert response["data"]["result"] == "test"
        assert mock_execute.call_count == 2


class TestErrorHandling:
    """錯誤處理測試"""
    
    def test_invalid_input_error(self):
        """無效輸入錯誤測試"""
        error = InvalidInputError("輸入無效", field="input", value="invalid")
        
        assert error.error_code == "INVALID_INPUT"
        assert error.message == "輸入無效"
        assert error.details["field"] == "input"
        assert error.details["value"] == "invalid"
    
    def test_schema_validation_error(self):
        """Schema驗證錯誤測試"""
        validation_errors = [
            {"path": ["name"], "message": "必需字段"}
        ]
        error = SchemaValidationError("Schema驗證失敗", validation_errors=validation_errors)
        
        assert error.error_code == "SCHEMA_VALIDATION_ERROR"
        assert error.details["validation_errors"] == validation_errors
    
    def test_token_limit_exceeded_error(self):
        """Token限制超出錯誤測試"""
        error = TokenLimitExceededError(
            "Token限制超出",
            current_tokens=5000,
            max_tokens=4000
        )
        
        assert error.error_code == "TOKEN_LIMIT_EXCEEDED"
        assert error.details["current_tokens"] == 5000
        assert error.details["max_tokens"] == 4000
    
    def test_provider_error(self):
        """提供商錯誤測試"""
        error = ProviderError(
            "API調用失敗",
            provider="openai",
            status_code=500,
            response_body="Internal Server Error"
        )
        
        assert error.error_code == "PROVIDER_ERROR"
        assert error.details["provider"] == "openai"
        assert error.details["status_code"] == 500


class TestIntegration:
    """集成測試"""
    
    @patch('llm_standard.adapters.OpenAIAdapter.call_api')
    def test_end_to_end_workflow(self, mock_call_api):
        """端到端工作流測試"""
        # 模擬API響應
        mock_call_api.return_value = {
            "choices": [{
                "message": {
                    "content": '{"name": "張三", "age": 25, "email": "zhangsan@example.com"}'
                }
            }],
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 75,
                "total_tokens": 225
            }
        }
        
        # 創建客戶端
        client = StandardLLMClient(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
            validate_instructions=True,
            validate_responses=True
        )
        
        # 創建指令
        instruction = client.create_instruction(
            instruction_type="extraction",
            description="從文本中提取用戶信息",
            output_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0, "maximum": 150},
                    "email": {"type": "string", "format": "email"}
                },
                "required": ["name", "age"]
            },
            constraints=["output_language: zh-CN", "format: json_only"]
        )
        
        # 執行指令
        user_input = "我叫張三，今年25歲，郵箱是zhangsan@example.com"
        response = client.execute(instruction, user_input)
        
        # 驗證響應
        assert response["status"] == "success"
        assert response["data"]["name"] == "張三"
        assert response["data"]["age"] == 25
        assert response["data"]["email"] == "zhangsan@example.com"
        
        # 驗證元數據
        metadata = response["metadata"]
        assert metadata["model_info"]["provider"] == "openai"
        assert metadata["model_info"]["model"] == "gpt-4"
        assert metadata["token_usage"]["total_tokens"] == 225
        assert "processing_time" in metadata
        assert "timestamp" in metadata


if __name__ == "__main__":
    # 運行測試
    pytest.main(["-v", __file__])