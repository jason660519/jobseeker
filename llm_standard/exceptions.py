"""LLM標準庫異常定義"""

class LLMStandardError(Exception):
    """LLM標準庫基礎異常類"""
    
    def __init__(self, message: str, error_code: str = None, details: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details
        self.message = message
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details,
            "severity": "error"
        }


class InvalidInputError(LLMStandardError):
    """輸入格式錯誤"""
    
    def __init__(self, message: str = "輸入格式錯誤", details: str = None):
        super().__init__(message, "E001", details)


class SchemaValidationError(LLMStandardError):
    """Schema驗證失敗"""
    
    def __init__(self, message: str = "Schema驗證失敗", details: str = None, field: str = None):
        super().__init__(message, "E002", details)
        self.field = field
    
    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.field:
            result["field"] = self.field
        return result


class TokenLimitExceededError(LLMStandardError):
    """超出token限制"""
    
    def __init__(self, message: str = "超出token限制", details: str = None):
        super().__init__(message, "E003", details)


class TimeoutError(LLMStandardError):
    """請求超時"""
    
    def __init__(self, message: str = "請求超時", details: str = None):
        super().__init__(message, "E004", details)


class ModelUnavailableError(LLMStandardError):
    """模型不可用"""
    
    def __init__(self, message: str = "模型不可用", details: str = None):
        super().__init__(message, "E005", details)


class RateLimitExceededError(LLMStandardError):
    """超出速率限制"""
    
    def __init__(self, message: str = "超出速率限制", details: str = None):
        super().__init__(message, "E006", details)


class ContentFilteredError(LLMStandardError):
    """內容被過濾"""
    
    def __init__(self, message: str = "內容被過濾", details: str = None):
        super().__init__(message, "E007", details)


class ParsingError(LLMStandardError):
    """解析錯誤"""
    
    def __init__(self, message: str = "解析錯誤", details: str = None):
        super().__init__(message, "E008", details)


# 錯誤代碼映射
ERROR_CODE_MAP = {
    "E001": InvalidInputError,
    "E002": SchemaValidationError,
    "E003": TokenLimitExceededError,
    "E004": TimeoutError,
    "E005": ModelUnavailableError,
    "E006": RateLimitExceededError,
    "E007": ContentFilteredError,
    "E008": ParsingError
}


def create_error_from_code(error_code: str, message: str = None, details: str = None) -> LLMStandardError:
    """根據錯誤代碼創建對應的異常實例"""
    error_class = ERROR_CODE_MAP.get(error_code, LLMStandardError)
    if error_class == LLMStandardError:
        return LLMStandardError(message or "未知錯誤", error_code, details)
    else:
        return error_class(message, details)