"""基本使用示例"""

import json
from llm_standard import StandardLLMClient


def example_structured_output():
    """結構化輸出示例"""
    print("=== 結構化輸出示例 ===")
    
    # 初始化客戶端
    client = StandardLLMClient(
        provider="openai",
        api_key="your-openai-api-key",
        model="gpt-4"
    )
    
    # 創建指令
    instruction = client.create_instruction(
        instruction_type="structured_output",
        description="從文本中提取用戶信息",
        output_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "用戶姓名"},
                "age": {"type": "integer", "description": "用戶年齡"},
                "email": {"type": "string", "format": "email", "description": "電子郵箱"},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "技能列表"
                }
            },
            "required": ["name", "age"]
        },
        constraints=[
            "output_language: zh-CN",
            "format: json_only",
            "validation: strict"
        ]
    )
    
    # 執行指令
    input_text = "我叫張三，今年28歲，是一名軟件工程師，擅長Python和JavaScript，郵箱是zhangsan@example.com"
    
    try:
        response = client.execute(instruction, input_text)
        
        print(f"狀態: {response['status']}")
        print(f"處理時間: {response['metadata']['processing_time']:.2f}秒")
        print(f"提取的信息: {json.dumps(response['data'], ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"錯誤: {e}")


def example_text_analysis():
    """文本分析示例"""
    print("\n=== 文本分析示例 ===")
    
    # 使用Anthropic
    client = StandardLLMClient(
        provider="anthropic",
        api_key="your-anthropic-api-key",
        model="claude-3-haiku-20240307"
    )
    
    # 創建分析指令
    instruction = client.create_instruction(
        instruction_type="analysis",
        description="分析文本的情感傾向和關鍵主題",
        output_schema={
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "情感傾向"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "置信度"
                },
                "key_themes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "關鍵主題"
                },
                "summary": {
                    "type": "string",
                    "description": "內容摘要"
                }
            },
            "required": ["sentiment", "confidence", "key_themes", "summary"]
        }
    )
    
    input_text = """
    今天的會議非常成功！我們團隊完成了季度目標，
    客戶對我們的產品非常滿意，銷售額超出預期30%。
    雖然過程中遇到了一些技術挑戰，但大家齊心協力解決了問題。
    我對團隊的表現感到非常驕傲，期待下個季度的更大突破。
    """
    
    try:
        response = client.execute(instruction, input_text)
        
        if response['status'] == 'success':
            data = response['data']
            print(f"情感傾向: {data['sentiment']}")
            print(f"置信度: {data['confidence']:.2f}")
            print(f"關鍵主題: {', '.join(data['key_themes'])}")
            print(f"摘要: {data['summary']}")
        else:
            print(f"分析失敗: {response['errors']}")
            
    except Exception as e:
        print(f"錯誤: {e}")


def example_classification():
    """分類示例"""
    print("\n=== 文本分類示例 ===")
    
    # 使用DeepSeek
    client = StandardLLMClient(
        provider="deepseek",
        api_key="your-deepseek-api-key",
        model="deepseek-chat"
    )
    
    # 創建分類指令
    instruction = client.create_instruction(
        instruction_type="classification",
        description="將客服對話分類到相應的業務類別",
        output_schema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["技術支持", "銷售諮詢", "退款申請", "產品建議", "投訴"],
                    "description": "業務類別"
                },
                "priority": {
                    "type": "string",
                    "enum": ["高", "中", "低"],
                    "description": "優先級"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "關鍵詞"
                },
                "suggested_action": {
                    "type": "string",
                    "description": "建議處理方式"
                }
            },
            "required": ["category", "priority", "keywords", "suggested_action"]
        }
    )
    
    input_text = """
    客戶: 你好，我購買的軟件無法正常啟動，已經嘗試重新安裝但問題依然存在。
    這個問題已經影響我的工作三天了，希望能盡快解決。我的訂單號是ORD123456。
    """
    
    try:
        response = client.execute(instruction, input_text)
        
        if response['status'] == 'success':
            data = response['data']
            print(f"分類: {data['category']}")
            print(f"優先級: {data['priority']}")
            print(f"關鍵詞: {', '.join(data['keywords'])}")
            print(f"建議處理: {data['suggested_action']}")
        else:
            print(f"分類失敗: {response['errors']}")
            
    except Exception as e:
        print(f"錯誤: {e}")


def example_batch_processing():
    """批量處理示例"""
    print("\n=== 批量處理示例 ===")
    
    client = StandardLLMClient(
        provider="openai",
        api_key="your-openai-api-key",
        model="gpt-3.5-turbo"
    )
    
    # 創建批量指令
    instruction = client.create_instruction(
        instruction_type="extraction",
        description="提取聯繫信息",
        output_schema={
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "電話號碼"},
                "email": {"type": "string", "description": "電子郵箱"},
                "company": {"type": "string", "description": "公司名稱"}
            }
        }
    )
    
    # 批量輸入
    input_texts = [
        "請聯繫張經理，電話：138-0013-8000，郵箱：zhang@abc.com，ABC科技公司",
        "李總監的聯繫方式：手機186-6666-8888，email: li@xyz.com，XYZ集團",
        "王助理：電話021-12345678，郵箱wang@def.com，DEF有限公司"
    ]
    
    instructions = [instruction] * len(input_texts)
    
    try:
        responses = client.execute_batch(instructions, input_texts)
        
        for i, response in enumerate(responses):
            print(f"\n結果 {i+1}:")
            if response['status'] == 'success':
                data = response['data']
                print(f"  電話: {data.get('phone', 'N/A')}")
                print(f"  郵箱: {data.get('email', 'N/A')}")
                print(f"  公司: {data.get('company', 'N/A')}")
            else:
                print(f"  錯誤: {response['errors']}")
                
    except Exception as e:
        print(f"批量處理錯誤: {e}")


def example_health_check():
    """健康檢查示例"""
    print("\n=== 健康檢查示例 ===")
    
    client = StandardLLMClient(
        provider="openai",
        api_key="your-openai-api-key",
        model="gpt-4"
    )
    
    # 執行健康檢查
    health_result = client.health_check()
    
    print(f"健康狀態: {health_result['status']}")
    print(f"提供商: {health_result['provider']}")
    print(f"模型: {health_result['model']}")
    
    if health_result['status'] == 'healthy':
        print(f"響應時間: {health_result['response_time']:.2f}秒")
    else:
        print(f"錯誤信息: {health_result['error']}")
    
    # 獲取支持的功能
    features = client.get_supported_features()
    print("\n支持的功能:")
    for feature, supported in features.items():
        status = "✅" if supported else "❌"
        print(f"  {feature}: {status}")


def example_error_handling():
    """錯誤處理示例"""
    print("\n=== 錯誤處理示例 ===")
    
    client = StandardLLMClient(
        provider="openai",
        api_key="invalid-key",  # 故意使用無效密鑰
        model="gpt-4"
    )
    
    instruction = client.create_instruction(
        instruction_type="text_generation",
        description="生成一段文本"
    )
    
    try:
        response = client.execute(instruction, "測試輸入")
        print(f"意外成功: {response}")
    except Exception as e:
        print(f"捕獲到錯誤: {type(e).__name__}: {e}")
        
        # 如果是標準錯誤，顯示詳細信息
        if hasattr(e, 'error_code'):
            print(f"錯誤代碼: {e.error_code}")
            print(f"錯誤詳情: {e.details}")


if __name__ == "__main__":
    # 運行所有示例
    print("LLM指令遵循與結構化輸出標準庫 - 使用示例")
    print("=" * 50)
    
    # 注意：運行前請設置正確的API密鑰
    print("注意：請在代碼中設置正確的API密鑰後運行示例")
    
    # example_structured_output()
    # example_text_analysis()
    # example_classification()
    # example_batch_processing()
    # example_health_check()
    # example_error_handling()
    
    print("\n所有示例完成！")