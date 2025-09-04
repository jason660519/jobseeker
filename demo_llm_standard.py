#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM指令遵循與結構化輸出標準庫 - 演示腳本

此腳本演示了LLM標準庫的核心功能，包括：
1. 基本的結構化輸出
2. 情感分析
3. 信息提取
4. 文本分類
5. 批量處理
6. 客戶端池負載均衡

使用方法:
    python demo_llm_standard.py

環境變量:
    OPENAI_API_KEY: OpenAI API密鑰
    或使用LiteLLM代理: LITELLM_PROXY_URL=http://localhost:4000
"""

import os
import sys
import json
import time
from typing import Dict, List, Any

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模擬LLM標準庫（實際使用時會從已安裝的包導入）
class MockStandardLLMClient:
    """模擬的LLM標準客戶端（用於演示）"""
    
    def __init__(self, provider: str, api_key: str, model: str, **kwargs):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get('base_url')
        self.timeout = kwargs.get('timeout', 30)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'total_tokens': 0,
            'total_time': 0.0
        }
    
    def create_instruction(self, instruction_type: str, description: str, output_schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """創建標準指令"""
        return {
            'instruction_type': instruction_type,
            'version': '1.0',
            'task': {
                'description': description,
                'context': kwargs.get('context', ''),
                'constraints': kwargs.get('constraints', [])
            },
            'output_schema': output_schema,
            'examples': kwargs.get('examples', []),
            'metadata': {
                'priority': kwargs.get('priority', 'medium'),
                'timeout': kwargs.get('timeout', self.timeout),
                'retry_count': kwargs.get('retry_count', 3)
            }
        }
    
    def execute(self, instruction: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """執行指令（模擬實現）"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # 模擬API調用延遲
            time.sleep(0.5 + (self.stats['total_requests'] % 3) * 0.2)
            
            # 根據指令類型生成模擬響應
            mock_data = self._generate_mock_response(instruction, user_input)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.stats['successful_requests'] += 1
            self.stats['total_time'] += duration
            self.stats['total_tokens'] += len(user_input.split()) * 2  # 模擬token計算
            
            return {
                'status': 'success',
                'data': mock_data,
                'metadata': {
                    'provider': self.provider,
                    'model': self.model,
                    'response_time': duration,
                    'tokens_used': len(user_input.split()) * 2,
                    'timestamp': time.time()
                },
                'errors': []
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'status': 'error',
                'data': None,
                'metadata': {
                    'provider': self.provider,
                    'model': self.model,
                    'response_time': duration,
                    'timestamp': time.time()
                },
                'errors': [str(e)]
            }
    
    def _generate_mock_response(self, instruction: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """生成模擬響應數據"""
        instruction_type = instruction['instruction_type']
        description = instruction['task']['description']
        
        # 情感分析
        if '情感' in description or 'sentiment' in description.lower():
            positive_words = ['好', '棒', '滿意', '推薦', '優秀', '喜歡', '不錯']
            negative_words = ['差', '糟', '失望', '貴', '爛', '討厭', '問題']
            
            positive_count = sum(1 for word in positive_words if word in user_input)
            negative_count = sum(1 for word in negative_words if word in user_input)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                confidence = 0.8 + (positive_count * 0.05)
            elif negative_count > positive_count:
                sentiment = 'negative'
                confidence = 0.8 + (negative_count * 0.05)
            else:
                sentiment = 'neutral'
                confidence = 0.6
            
            confidence = min(confidence, 1.0)
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence, 2),
                'keywords': [word for word in positive_words + negative_words if word in user_input]
            }
        
        # 信息提取
        elif '提取' in description or 'extraction' in description.lower():
            import re
            
            # 提取姓名（中文姓名模式）
            name_pattern = r'[我叫|姓名是|名字是]?([\u4e00-\u9fa5]{2,4})'
            name_match = re.search(name_pattern, user_input)
            name = name_match.group(1) if name_match else '未知'
            
            # 提取年齡
            age_pattern = r'(\d{1,2})歲'
            age_match = re.search(age_pattern, user_input)
            age = int(age_match.group(1)) if age_match else None
            
            # 提取郵箱
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_match = re.search(email_pattern, user_input)
            email = email_match.group(0) if email_match else None
            
            # 提取電話
            phone_pattern = r'[+]?[0-9-]{10,15}'
            phone_match = re.search(phone_pattern, user_input)
            phone = phone_match.group(0) if phone_match else None
            
            # 提取技能
            skill_keywords = ['Python', 'Java', 'JavaScript', 'C++', 'Go', 'Rust', '機器學習', '深度學習', 
                            'Spring', '數據庫', 'MySQL', 'PostgreSQL', 'Redis', 'Docker', 'Kubernetes']
            skills = [skill for skill in skill_keywords if skill in user_input]
            
            result = {'name': name}
            if age is not None:
                result['age'] = age
            if email:
                result['email'] = email
            if phone:
                result['phone'] = phone
            if skills:
                result['skills'] = skills
            
            return result
        
        # 文本分類
        elif '分類' in description or 'classification' in description.lower():
            tech_keywords = ['技術', '人工智能', 'AI', '機器學習', '深度學習', '算法', '編程', '軟件', '硬件']
            business_keywords = ['商業', '股市', '投資', '經濟', '金融', '市場', '銷售', '管理']
            entertainment_keywords = ['娛樂', '電影', '音樂', '遊戲', '明星', '綜藝', '小說']
            sports_keywords = ['體育', '運動', '足球', '籃球', '網球', '游泳', '健身', '比賽']
            health_keywords = ['健康', '醫療', '疾病', '治療', '藥物', '醫院', '醫生', '養生']
            
            categories = {
                '技術': tech_keywords,
                '商業': business_keywords,
                '娛樂': entertainment_keywords,
                '體育': sports_keywords,
                '健康': health_keywords
            }
            
            max_score = 0
            best_category = '其他'
            
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in user_input)
                if score > max_score:
                    max_score = score
                    best_category = category
            
            confidence = min(0.6 + (max_score * 0.1), 0.95) if max_score > 0 else 0.3
            
            return {
                'category': best_category,
                'confidence': round(confidence, 2),
                'subcategory': f'{best_category}相關' if best_category != '其他' else '未分類'
            }
        
        # 默認響應
        else:
            return {
                'message': f'已處理輸入: {user_input[:50]}...',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'provider': self.provider
            }
    
    def batch_execute(self, instruction: Dict[str, Any], inputs: List[str]) -> List[Dict[str, Any]]:
        """批量執行指令"""
        results = []
        for user_input in inputs:
            result = self.execute(instruction, user_input)
            results.append(result)
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            'status': 'healthy',
            'provider': self.provider,
            'model': self.model,
            'timestamp': time.time()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        if self.stats['total_requests'] > 0:
            success_rate = self.stats['successful_requests'] / self.stats['total_requests']
            avg_response_time = self.stats['total_time'] / self.stats['total_requests']
        else:
            success_rate = 0.0
            avg_response_time = 0.0
        
        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_tokens': self.stats['total_tokens']
        }


class MockLLMClientPool:
    """模擬的客戶端池"""
    
    def __init__(self, clients: List[MockStandardLLMClient]):
        self.clients = clients
        self.current_index = 0
        self.pool_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'total_time': 0.0
        }
    
    def execute(self, instruction: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """使用負載均衡執行指令"""
        start_time = time.time()
        self.pool_stats['total_requests'] += 1
        
        # 輪詢選擇客戶端
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.clients)
        
        try:
            result = client.execute(instruction, user_input)
            
            if result['status'] == 'success':
                self.pool_stats['successful_requests'] += 1
            
            end_time = time.time()
            self.pool_stats['total_time'] += (end_time - start_time)
            
            return result
            
        except Exception as e:
            # 故障轉移到下一個客戶端
            if len(self.clients) > 1:
                fallback_client = self.clients[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.clients)
                return fallback_client.execute(instruction, user_input)
            else:
                raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取池統計信息"""
        if self.pool_stats['total_requests'] > 0:
            success_rate = self.pool_stats['successful_requests'] / self.pool_stats['total_requests']
            avg_response_time = self.pool_stats['total_time'] / self.pool_stats['total_requests']
        else:
            success_rate = 0.0
            avg_response_time = 0.0
        
        return {
            'total_requests': self.pool_stats['total_requests'],
            'successful_requests': self.pool_stats['successful_requests'],
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'active_clients': len(self.clients)
        }


def demo_basic_usage():
    """演示基本使用"""
    print("\n🚀 演示1: 基本結構化輸出")
    print("-" * 50)
    
    # 創建客戶端
    client = MockStandardLLMClient(
        provider="openai",
        api_key="demo-key",
        model="gpt-3.5-turbo"
    )
    
    # 創建簡單指令
    instruction = client.create_instruction(
        instruction_type="structured_output",
        description="生成一個友好的問候消息",
        output_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "timestamp": {"type": "string"},
                "provider": {"type": "string"}
            },
            "required": ["message"]
        }
    )
    
    # 執行指令
    response = client.execute(instruction, "請向我問好")
    
    if response['status'] == 'success':
        data = response['data']
        print(f"✅ 執行成功!")
        print(f"   消息: {data['message']}")
        print(f"   時間戳: {data.get('timestamp', 'N/A')}")
        print(f"   提供商: {data.get('provider', 'N/A')}")
        print(f"   響應時間: {response['metadata']['response_time']:.2f}秒")
    else:
        print(f"❌ 執行失敗: {response['errors']}")


def demo_sentiment_analysis():
    """演示情感分析"""
    print("\n💭 演示2: 情感分析")
    print("-" * 50)
    
    client = MockStandardLLMClient(
        provider="anthropic",
        api_key="demo-key",
        model="claude-3-haiku"
    )
    
    # 創建情感分析指令
    instruction = client.create_instruction(
        instruction_type="text_analysis",
        description="分析文本的情感傾向",
        output_schema={
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["sentiment", "confidence"]
        }
    )
    
    # 測試不同情感的文本
    test_texts = [
        "這個產品真的很棒，我非常滿意！",
        "服務態度一般，還有改進空間。",
        "價格太貴了，性價比不高。",
        "質量不錯，值得推薦給朋友。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 測試文本 {i}: {text}")
        response = client.execute(instruction, text)
        
        if response['status'] == 'success':
            data = response['data']
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😞',
                'neutral': '😐'
            }
            
            print(f"   情感: {data['sentiment']} {sentiment_emoji.get(data['sentiment'], '')}")
            print(f"   置信度: {data['confidence']:.2f}")
            if data.get('keywords'):
                print(f"   關鍵詞: {', '.join(data['keywords'])}")
        else:
            print(f"   ❌ 分析失敗: {response['errors']}")


def demo_information_extraction():
    """演示信息提取"""
    print("\n🔍 演示3: 信息提取")
    print("-" * 50)
    
    client = MockStandardLLMClient(
        provider="google",
        api_key="demo-key",
        model="gemini-pro"
    )
    
    # 創建信息提取指令
    instruction = client.create_instruction(
        instruction_type="extraction",
        description="從文本中提取個人信息",
        output_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["name"]
        }
    )
    
    # 測試文本
    test_texts = [
        "我叫張三，今年28歲，郵箱是zhangsan@example.com，電話是+86-13812345678，擅長Python和機器學習。",
        "李四，25歲，聯繫方式：lisi@company.com，手機：+86-15987654321，技能：Java、Spring、數據庫設計。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📄 測試文本 {i}: {text}")
        response = client.execute(instruction, text)
        
        if response['status'] == 'success':
            data = response['data']
            print(f"   姓名: {data.get('name', 'N/A')}")
            print(f"   年齡: {data.get('age', 'N/A')}")
            print(f"   郵箱: {data.get('email', 'N/A')}")
            print(f"   電話: {data.get('phone', 'N/A')}")
            if data.get('skills'):
                print(f"   技能: {', '.join(data['skills'])}")
        else:
            print(f"   ❌ 提取失敗: {response['errors']}")


def demo_text_classification():
    """演示文本分類"""
    print("\n📊 演示4: 文本分類")
    print("-" * 50)
    
    client = MockStandardLLMClient(
        provider="deepseek",
        api_key="demo-key",
        model="deepseek-chat"
    )
    
    # 創建分類指令
    instruction = client.create_instruction(
        instruction_type="classification",
        description="對文本進行主題分類",
        output_schema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["技術", "商業", "娛樂", "體育", "健康", "其他"]
                },
                "subcategory": {"type": "string"},
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "required": ["category", "confidence"]
        }
    )
    
    # 測試文本
    test_texts = [
        "人工智能技術在醫療診斷中的應用越來越廣泛。",
        "今年的股市表現超出了大多數投資者的預期。",
        "新上映的科幻電影獲得了觀眾的一致好評。",
        "職業籃球聯賽的季後賽即將開始。",
        "研究表明，定期運動有助於提高免疫力。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📰 測試文本 {i}: {text}")
        response = client.execute(instruction, text)
        
        if response['status'] == 'success':
            data = response['data']
            category_emoji = {
                '技術': '💻',
                '商業': '💼',
                '娛樂': '🎬',
                '體育': '⚽',
                '健康': '🏥',
                '其他': '📝'
            }
            
            print(f"   分類: {data['category']} {category_emoji.get(data['category'], '')}")
            print(f"   子分類: {data.get('subcategory', 'N/A')}")
            print(f"   置信度: {data['confidence']:.2f}")
        else:
            print(f"   ❌ 分類失敗: {response['errors']}")


def demo_batch_processing():
    """演示批量處理"""
    print("\n📦 演示5: 批量處理")
    print("-" * 50)
    
    client = MockStandardLLMClient(
        provider="openai",
        api_key="demo-key",
        model="gpt-4"
    )
    
    # 創建批量情感分析指令
    instruction = client.create_instruction(
        instruction_type="text_analysis",
        description="批量分析用戶評論的情感",
        output_schema={
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "required": ["sentiment", "confidence"]
        }
    )
    
    # 批量輸入
    batch_inputs = [
        "產品質量很好，值得購買！",
        "配送速度太慢了，不滿意。",
        "價格合理，服務一般。",
        "包裝精美，超出預期！",
        "客服態度很差，體驗不好。"
    ]
    
    print(f"📝 處理 {len(batch_inputs)} 條用戶評論...")
    
    start_time = time.time()
    responses = client.batch_execute(instruction, batch_inputs)
    end_time = time.time()
    
    batch_duration = end_time - start_time
    
    print(f"\n⏱️ 批量處理完成，耗時: {batch_duration:.2f}秒")
    print(f"📊 平均每條: {batch_duration/len(batch_inputs):.2f}秒")
    
    # 統計結果
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for i, (input_text, response) in enumerate(zip(batch_inputs, responses), 1):
        print(f"\n{i}. {input_text}")
        if response['status'] == 'success':
            data = response['data']
            sentiment = data['sentiment']
            confidence = data['confidence']
            sentiment_counts[sentiment] += 1
            
            emoji = {'positive': '😊', 'negative': '😞', 'neutral': '😐'}
            print(f"   → {sentiment} {emoji[sentiment]} (置信度: {confidence:.2f})")
        else:
            print(f"   → ❌ 處理失敗: {response['errors']}")
    
    print(f"\n📈 情感分布統計:")
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(batch_inputs)) * 100
        print(f"   {sentiment}: {count} 條 ({percentage:.1f}%)")


def demo_client_pool():
    """演示客戶端池負載均衡"""
    print("\n⚖️ 演示6: 客戶端池負載均衡")
    print("-" * 50)
    
    # 創建多個客戶端
    clients = [
        MockStandardLLMClient(provider="openai", api_key="key1", model="gpt-4"),
        MockStandardLLMClient(provider="anthropic", api_key="key2", model="claude-3-haiku"),
        MockStandardLLMClient(provider="google", api_key="key3", model="gemini-pro")
    ]
    
    # 創建客戶端池
    pool = MockLLMClientPool(clients)
    
    print(f"🔧 創建了包含 {len(clients)} 個客戶端的池")
    
    # 創建測試指令
    instruction = clients[0].create_instruction(
        instruction_type="structured_output",
        description="測試負載均衡",
        output_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "provider": {"type": "string"}
            },
            "required": ["message"]
        }
    )
    
    # 執行多次請求測試負載均衡
    test_requests = [f"測試請求 {i+1}" for i in range(6)]
    
    print(f"\n🔄 執行 {len(test_requests)} 個請求測試負載均衡...")
    
    start_time = time.time()
    
    for i, request in enumerate(test_requests, 1):
        response = pool.execute(instruction, request)
        
        if response['status'] == 'success':
            provider = response['metadata']['provider']
            response_time = response['metadata']['response_time']
            print(f"   {i}. {request} → {provider} (耗時: {response_time:.2f}秒)")
        else:
            print(f"   {i}. {request} → ❌ 失敗")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 獲取池統計信息
    pool_stats = pool.get_stats()
    
    print(f"\n📊 客戶端池統計:")
    print(f"   總請求數: {pool_stats['total_requests']}")
    print(f"   成功請求數: {pool_stats['successful_requests']}")
    print(f"   成功率: {pool_stats['success_rate']:.2%}")
    print(f"   平均響應時間: {pool_stats['avg_response_time']:.2f}秒")
    print(f"   總耗時: {total_time:.2f}秒")
    
    # 顯示各客戶端的使用情況
    print(f"\n🔍 各客戶端使用情況:")
    for i, client in enumerate(clients, 1):
        stats = client.get_stats()
        print(f"   客戶端 {i} ({client.provider}): {stats['total_requests']} 請求")


def demo_performance_monitoring():
    """演示性能監控"""
    print("\n📈 演示7: 性能監控")
    print("-" * 50)
    
    client = MockStandardLLMClient(
        provider="openai",
        api_key="demo-key",
        model="gpt-3.5-turbo"
    )
    
    # 創建測試指令
    instruction = client.create_instruction(
        instruction_type="structured_output",
        description="性能測試指令",
        output_schema={
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }
    )
    
    # 執行多次請求收集性能數據
    print("🔄 執行性能測試...")
    
    test_count = 10
    response_times = []
    
    for i in range(test_count):
        start_time = time.time()
        response = client.execute(instruction, f"性能測試 {i+1}")
        end_time = time.time()
        
        if response['status'] == 'success':
            response_time = response['metadata']['response_time']
            response_times.append(response_time)
            print(f"   請求 {i+1}: {response_time:.3f}秒")
        else:
            print(f"   請求 {i+1}: 失敗")
    
    # 計算性能統計
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n📊 性能統計:")
        print(f"   總請求數: {test_count}")
        print(f"   成功請求數: {len(response_times)}")
        print(f"   成功率: {len(response_times)/test_count:.2%}")
        print(f"   平均響應時間: {avg_time:.3f}秒")
        print(f"   最快響應時間: {min_time:.3f}秒")
        print(f"   最慢響應時間: {max_time:.3f}秒")
    
    # 健康檢查
    print(f"\n🏥 健康檢查:")
    health = client.health_check()
    print(f"   狀態: {health['status']}")
    print(f"   提供商: {health['provider']}")
    print(f"   模型: {health['model']}")
    
    # 客戶端統計
    stats = client.get_stats()
    print(f"\n📋 客戶端統計:")
    print(f"   總請求數: {stats['total_requests']}")
    print(f"   成功請求數: {stats['successful_requests']}")
    print(f"   成功率: {stats['success_rate']:.2%}")
    print(f"   平均響應時間: {stats['avg_response_time']:.3f}秒")
    print(f"   總Token使用: {stats['total_tokens']}")


def main():
    """主函數"""
    print("🎯 LLM指令遵循與結構化輸出標準庫 - 功能演示")
    print("=" * 60)
    print("版本: 1.0.0")
    print("作者: JobSpy Team")
    print("\n本演示使用模擬客戶端展示標準庫的核心功能")
    print("實際使用時，請配置真實的API密鑰")
    print("=" * 60)
    
    # 運行所有演示
    demos = [
        demo_basic_usage,
        demo_sentiment_analysis,
        demo_information_extraction,
        demo_text_classification,
        demo_batch_processing,
        demo_client_pool,
        demo_performance_monitoring
    ]
    
    for demo in demos:
        try:
            demo()
            time.sleep(1)  # 演示間隔
        except KeyboardInterrupt:
            print("\n\n⏹️ 演示被用戶中斷")
            break
        except Exception as e:
            print(f"\n❌ 演示異常: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("\n📚 更多信息:")
    print("   - 查看 README_LLM_STANDARD.md 了解詳細文檔")
    print("   - 運行 test_llm_standard_integration.py 進行完整測試")
    print("   - 查看 examples/ 目錄了解更多使用示例")
    print("=" * 60)


if __name__ == '__main__':
    main()