"""Schema驗證器模組"""

import json
import jsonschema
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

from .exceptions import SchemaValidationError, ParsingError


class SchemaValidator:
    """JSON Schema驗證器"""
    
    def __init__(self):
        self.validator_cache = {}
    
    def validate(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        驗證數據是否符合Schema
        
        Args:
            data: 要驗證的數據
            schema: JSON Schema定義
            
        Returns:
            Tuple[bool, List[str]]: (是否通過驗證, 錯誤信息列表)
        """
        try:
            # 創建驗證器
            validator = self._get_validator(schema)
            
            # 執行驗證
            errors = list(validator.iter_errors(data))
            
            if errors:
                error_messages = [self._format_error(error) for error in errors]
                return False, error_messages
            
            return True, []
            
        except Exception as e:
            return False, [f"驗證過程中發生錯誤: {str(e)}"]
    
    def validate_strict(self, data: Any, schema: Dict[str, Any]) -> None:
        """
        嚴格驗證，失敗時拋出異常
        
        Args:
            data: 要驗證的數據
            schema: JSON Schema定義
            
        Raises:
            SchemaValidationError: 驗證失敗時拋出
        """
        is_valid, errors = self.validate(data, schema)
        if not is_valid:
            error_details = "; ".join(errors)
            raise SchemaValidationError(
                message="數據不符合Schema規範",
                details=error_details
            )
    
    def _get_validator(self, schema: Dict[str, Any]) -> jsonschema.protocols.Validator:
        """獲取驗證器（帶緩存）"""
        schema_key = json.dumps(schema, sort_keys=True)
        
        if schema_key not in self.validator_cache:
            # 擴展Schema以支持自定義格式
            extended_schema = self._extend_schema(schema)
            validator_class = jsonschema.validators.validator_for(extended_schema)
            validator_class.check_schema(extended_schema)
            self.validator_cache[schema_key] = validator_class(extended_schema)
        
        return self.validator_cache[schema_key]
    
    def _extend_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """擴展Schema以支持自定義格式驗證"""
        extended_schema = schema.copy()
        
        # 添加自定義格式驗證器
        format_checker = jsonschema.FormatChecker()
        
        # 註冊自定義格式
        @format_checker.checks('datetime-iso8601')
        def check_datetime_iso8601(instance):
            """驗證ISO 8601日期時間格式"""
            try:
                datetime.fromisoformat(instance.replace('Z', '+00:00'))
                return True
            except ValueError:
                return False
        
        @format_checker.checks('phone-number')
        def check_phone_number(instance):
            """驗證電話號碼格式"""
            pattern = r'^\+?[1-9]\d{1,14}$|^\+?\d{1,4}[\s\-]?\d{1,14}$'
            return bool(re.match(pattern, instance))
        
        @format_checker.checks('chinese-name')
        def check_chinese_name(instance):
            """驗證中文姓名格式"""
            pattern = r'^[\u4e00-\u9fa5]{2,10}$'
            return bool(re.match(pattern, instance))
        
        return extended_schema
    
    def _format_error(self, error: jsonschema.ValidationError) -> str:
        """格式化驗證錯誤信息"""
        path = "." + ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "根節點"
        return f"字段 '{path}': {error.message}"


class ResponseValidator:
    """響應格式驗證器"""
    
    # 標準響應Schema
    STANDARD_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["success", "error", "partial"]
            },
            "timestamp": {
                "type": "string",
                "format": "datetime-iso8601"
            },
            "model_info": {
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "enum": ["openai", "anthropic", "google", "deepseek"]
                    },
                    "model": {"type": "string"},
                    "version": {"type": "string"}
                },
                "required": ["provider", "model"]
            },
            "request_id": {"type": "string"},
            "data": {"type": "object"},
            "metadata": {
                "type": "object",
                "properties": {
                    "processing_time": {"type": "number", "minimum": 0},
                    "token_usage": {
                        "type": "object",
                        "properties": {
                            "prompt_tokens": {"type": "integer", "minimum": 0},
                            "completion_tokens": {"type": "integer", "minimum": 0},
                            "total_tokens": {"type": "integer", "minimum": 0}
                        },
                        "required": ["prompt_tokens", "completion_tokens", "total_tokens"]
                    },
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
                }
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "details": {"type": "string"},
                        "field": {"type": "string"},
                        "severity": {"type": "string", "enum": ["error", "warning"]}
                    },
                    "required": ["code", "message", "severity"]
                }
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "details": {"type": "string"}
                    },
                    "required": ["code", "message"]
                }
            }
        },
        "required": ["status", "timestamp", "model_info", "request_id"]
    }
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
    
    def validate_response(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        驗證響應是否符合標準格式
        
        Args:
            response: 響應數據
            
        Returns:
            Tuple[bool, List[str]]: (是否通過驗證, 錯誤信息列表)
        """
        return self.schema_validator.validate(response, self.STANDARD_RESPONSE_SCHEMA)
    
    def validate_response_strict(self, response: Dict[str, Any]) -> None:
        """
        嚴格驗證響應格式
        
        Args:
            response: 響應數據
            
        Raises:
            SchemaValidationError: 驗證失敗時拋出
        """
        self.schema_validator.validate_strict(response, self.STANDARD_RESPONSE_SCHEMA)


class InstructionValidator:
    """指令格式驗證器"""
    
    # 標準指令Schema
    STANDARD_INSTRUCTION_SCHEMA = {
        "type": "object",
        "properties": {
            "instruction_type": {
                "type": "string",
                "enum": ["structured_output", "text_generation", "analysis", "extraction", "classification", "summarization"]
            },
            "version": {"type": "string"},
            "task": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "context": {"type": "string"},
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["description"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "properties": {"type": "object"},
                    "required": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["type", "properties"]
            },
            "examples": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"},
                        "output": {"type": "object"}
                    },
                    "required": ["input", "output"]
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "timeout": {"type": "number", "minimum": 1},
                    "retry_count": {"type": "integer", "minimum": 0, "maximum": 10}
                }
            }
        },
        "required": ["instruction_type", "version", "task"]
    }
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
    
    def validate_instruction(self, instruction: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        驗證指令是否符合標準格式
        
        Args:
            instruction: 指令數據
            
        Returns:
            Tuple[bool, List[str]]: (是否通過驗證, 錯誤信息列表)
        """
        return self.schema_validator.validate(instruction, self.STANDARD_INSTRUCTION_SCHEMA)
    
    def validate_instruction_strict(self, instruction: Dict[str, Any]) -> None:
        """
        嚴格驗證指令格式
        
        Args:
            instruction: 指令數據
            
        Raises:
            SchemaValidationError: 驗證失敗時拋出
        """
        self.schema_validator.validate_strict(instruction, self.STANDARD_INSTRUCTION_SCHEMA)