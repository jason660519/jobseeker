#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM指令遵循與結構化輸出標準庫 - 集成測試腳本

此腳本用於測試LLM標準庫的完整功能，包括：
- 基本指令執行
- 結構化輸出驗證
- 多提供商支持
- 錯誤處理
- 性能測試
- 客戶端池功能

使用方法:
    python test_llm_standard_integration.py

環境變量:
    OPENAI_API_KEY: OpenAI API密鑰
    ANTHROPIC_API_KEY: Anthropic API密鑰
    GOOGLE_API_KEY: Google API密鑰
    DEEPSEEK_API_KEY: DeepSeek API密鑰
    LITELLM_PROXY_URL: LiteLLM代理服務器URL (默認: http://localhost:4000)
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from llm_standard import StandardLLMClient
    from llm_standard.client import LLMClientPool
    from llm_standard.exceptions import *
    from llm_standard.config import StandardConfig
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保已安裝LLM標準庫依賴: pip install -r requirements_llm_standard.txt")
    sys.exit(1)


class LLMStandardTester:
    """LLM標準庫測試器"""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'performance_metrics': {}
        }
        self.clients = {}
        self.test_data = self._prepare_test_data()
    
    def _prepare_test_data(self) -> Dict[str, Any]:
        """準備測試數據"""
        return {
            'sentiment_analysis': {
                'instruction_type': 'structured_output',
                'description': '分析文本的情感傾向',
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'sentiment': {
                            'type': 'string',
                            'enum': ['positive', 'negative', 'neutral']
                        },
                        'confidence': {
                            'type': 'number',
                            'minimum': 0,
                            'maximum': 1
                        },
                        'keywords': {
                            'type': 'array',
                            'items': {'type': 'string'}
                        }
                    },
                    'required': ['sentiment', 'confidence']
                },
                'test_inputs': [
                    '這個產品真的很棒，我非常滿意！',
                    '服務態度一般，還有改進空間。',
                    '價格太貴了，性價比不高。',
                    '質量不錯，值得推薦給朋友。'
                ]
            },
            'text_extraction': {
                'instruction_type': 'extraction',
                'description': '從文本中提取結構化信息',
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'age': {'type': 'integer', 'minimum': 0, 'maximum': 150},
                        'email': {'type': 'string', 'format': 'email-address'},
                        'phone': {'type': 'string', 'format': 'phone-number'},
                        'skills': {
                            'type': 'array',
                            'items': {'type': 'string'}
                        }
                    },
                    'required': ['name']
                },
                'test_inputs': [
                    '我叫張三，今年28歲，郵箱是zhangsan@example.com，電話是+86-13812345678，擅長Python和機器學習。',
                    '李四，25歲，聯繫方式：lisi@company.com，手機：+86-15987654321，技能：Java、Spring、數據庫設計。'
                ]
            },
            'classification': {
                'instruction_type': 'classification',
                'description': '對文本進行分類',
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'category': {
                            'type': 'string',
                            'enum': ['技術', '商業', '娛樂', '體育', '健康', '其他']
                        },
                        'subcategory': {'type': 'string'},
                        'confidence': {
                            'type': 'number',
                            'minimum': 0,
                            'maximum': 1
                        }
                    },
                    'required': ['category', 'confidence']
                },
                'test_inputs': [
                    '人工智能技術在醫療診斷中的應用越來越廣泛。',
                    '今年的股市表現超出了大多數投資者的預期。',
                    '新上映的科幻電影獲得了觀眾的一致好評。'
                ]
            }
        }
    
    def _setup_clients(self) -> None:
        """設置測試客戶端"""
        print("🔧 設置測試客戶端...")
        
        # OpenAI客戶端
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.clients['openai'] = StandardLLMClient(
                    provider='openai',
                    api_key=os.getenv('OPENAI_API_KEY'),
                    model='gpt-3.5-turbo',
                    timeout=30
                )
                print("✅ OpenAI客戶端設置成功")
            except Exception as e:
                print(f"❌ OpenAI客戶端設置失敗: {e}")
        
        # Anthropic客戶端
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                self.clients['anthropic'] = StandardLLMClient(
                    provider='anthropic',
                    api_key=os.getenv('ANTHROPIC_API_KEY'),
                    model='claude-3-haiku-20240307',
                    timeout=30
                )
                print("✅ Anthropic客戶端設置成功")
            except Exception as e:
                print(f"❌ Anthropic客戶端設置失敗: {e}")
        
        # LiteLLM代理客戶端
        litellm_url = os.getenv('LITELLM_PROXY_URL', 'http://localhost:4000')
        try:
            self.clients['litellm'] = StandardLLMClient(
                provider='openai',
                api_key='sk-1234',
                model='claude-3-haiku',
                base_url=litellm_url,
                timeout=30
            )
            print("✅ LiteLLM代理客戶端設置成功")
        except Exception as e:
            print(f"❌ LiteLLM代理客戶端設置失敗: {e}")
        
        if not self.clients:
            print("❌ 沒有可用的客戶端，請設置相應的API密鑰")
            sys.exit(1)
        
        print(f"📊 總共設置了 {len(self.clients)} 個客戶端")
    
    def _run_test(self, test_name: str, test_func) -> bool:
        """運行單個測試"""
        self.results['total_tests'] += 1
        try:
            print(f"\n🧪 運行測試: {test_name}")
            start_time = time.time()
            
            result = test_func()
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result:
                self.results['passed_tests'] += 1
                print(f"✅ 測試通過: {test_name} (耗時: {duration:.2f}秒)")
                return True
            else:
                self.results['failed_tests'] += 1
                print(f"❌ 測試失敗: {test_name} (耗時: {duration:.2f}秒)")
                return False
                
        except Exception as e:
            self.results['failed_tests'] += 1
            error_msg = f"測試異常: {test_name} - {str(e)}"
            self.results['errors'].append(error_msg)
            print(f"💥 {error_msg}")
            return False
    
    def test_basic_instruction_execution(self) -> bool:
        """測試基本指令執行"""
        for client_name, client in self.clients.items():
            try:
                # 創建簡單指令
                instruction = client.create_instruction(
                    instruction_type='structured_output',
                    description='返回一個簡單的問候消息',
                    output_schema={
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'},
                            'timestamp': {'type': 'string'}
                        },
                        'required': ['message']
                    }
                )
                
                # 執行指令
                response = client.execute(instruction, '請說你好')
                
                if response['status'] != 'success':
                    print(f"❌ {client_name}: 指令執行失敗 - {response.get('errors', [])}")
                    return False
                
                data = response['data']
                if 'message' not in data:
                    print(f"❌ {client_name}: 響應缺少必需字段 'message'")
                    return False
                
                print(f"✅ {client_name}: 基本指令執行成功 - {data['message'][:50]}...")
                
            except Exception as e:
                print(f"❌ {client_name}: 基本指令執行異常 - {e}")
                return False
        
        return True
    
    def test_structured_output_validation(self) -> bool:
        """測試結構化輸出驗證"""
        test_case = self.test_data['sentiment_analysis']
        
        for client_name, client in self.clients.items():
            try:
                # 創建指令
                instruction = client.create_instruction(
                    instruction_type=test_case['instruction_type'],
                    description=test_case['description'],
                    output_schema=test_case['output_schema']
                )
                
                # 測試每個輸入
                for test_input in test_case['test_inputs'][:2]:  # 只測試前兩個以節省時間
                    response = client.execute(instruction, test_input)
                    
                    if response['status'] != 'success':
                        print(f"❌ {client_name}: 結構化輸出失敗 - {response.get('errors', [])}")
                        return False
                    
                    data = response['data']
                    
                    # 驗證必需字段
                    if 'sentiment' not in data or 'confidence' not in data:
                        print(f"❌ {client_name}: 響應缺少必需字段")
                        return False
                    
                    # 驗證數據類型
                    if not isinstance(data['confidence'], (int, float)):
                        print(f"❌ {client_name}: confidence字段類型錯誤")
                        return False
                    
                    # 驗證枚舉值
                    if data['sentiment'] not in ['positive', 'negative', 'neutral']:
                        print(f"❌ {client_name}: sentiment值不在允許範圍內")
                        return False
                    
                    print(f"✅ {client_name}: 結構化輸出驗證成功 - {data['sentiment']} ({data['confidence']:.2f})")
                
            except Exception as e:
                print(f"❌ {client_name}: 結構化輸出驗證異常 - {e}")
                return False
        
        return True
    
    def test_batch_processing(self) -> bool:
        """測試批量處理"""
        test_case = self.test_data['classification']
        
        for client_name, client in self.clients.items():
            try:
                # 創建指令
                instruction = client.create_instruction(
                    instruction_type=test_case['instruction_type'],
                    description=test_case['description'],
                    output_schema=test_case['output_schema']
                )
                
                # 批量執行
                start_time = time.time()
                responses = client.batch_execute(instruction, test_case['test_inputs'])
                end_time = time.time()
                
                batch_duration = end_time - start_time
                
                if len(responses) != len(test_case['test_inputs']):
                    print(f"❌ {client_name}: 批量處理響應數量不匹配")
                    return False
                
                success_count = sum(1 for r in responses if r['status'] == 'success')
                
                if success_count == 0:
                    print(f"❌ {client_name}: 批量處理全部失敗")
                    return False
                
                print(f"✅ {client_name}: 批量處理成功 - {success_count}/{len(responses)} (耗時: {batch_duration:.2f}秒)")
                
                # 記錄性能指標
                if client_name not in self.results['performance_metrics']:
                    self.results['performance_metrics'][client_name] = {}
                
                self.results['performance_metrics'][client_name]['batch_processing'] = {
                    'total_requests': len(test_case['test_inputs']),
                    'successful_requests': success_count,
                    'total_time': batch_duration,
                    'avg_time_per_request': batch_duration / len(test_case['test_inputs'])
                }
                
            except Exception as e:
                print(f"❌ {client_name}: 批量處理異常 - {e}")
                return False
        
        return True
    
    def test_error_handling(self) -> bool:
        """測試錯誤處理"""
        for client_name, client in self.clients.items():
            try:
                # 測試無效Schema
                try:
                    invalid_instruction = client.create_instruction(
                        instruction_type='structured_output',
                        description='測試無效Schema',
                        output_schema={
                            'type': 'invalid_type',  # 無效類型
                            'properties': {}
                        }
                    )
                    
                    response = client.execute(invalid_instruction, '測試輸入')
                    
                    # 應該返回錯誤
                    if response['status'] == 'success':
                        print(f"❌ {client_name}: 應該檢測到無效Schema但沒有")
                        return False
                    
                    print(f"✅ {client_name}: 正確檢測到無效Schema")
                    
                except (InvalidInputError, SchemaValidationError) as e:
                    print(f"✅ {client_name}: 正確拋出Schema驗證異常 - {type(e).__name__}")
                
                # 測試空輸入
                try:
                    valid_instruction = client.create_instruction(
                        instruction_type='structured_output',
                        description='測試空輸入處理',
                        output_schema={
                            'type': 'object',
                            'properties': {
                                'result': {'type': 'string'}
                            },
                            'required': ['result']
                        }
                    )
                    
                    response = client.execute(valid_instruction, '')
                    
                    # 空輸入應該能處理或返回適當錯誤
                    if response['status'] == 'error':
                        print(f"✅ {client_name}: 正確處理空輸入錯誤")
                    else:
                        print(f"✅ {client_name}: 成功處理空輸入")
                    
                except Exception as e:
                    print(f"✅ {client_name}: 正確拋出空輸入異常 - {type(e).__name__}")
                
            except Exception as e:
                print(f"❌ {client_name}: 錯誤處理測試異常 - {e}")
                return False
        
        return True
    
    def test_client_pool(self) -> bool:
        """測試客戶端池功能"""
        if len(self.clients) < 2:
            print("⚠️ 客戶端數量不足，跳過客戶端池測試")
            return True
        
        try:
            # 創建客戶端池
            client_list = list(self.clients.values())
            pool = LLMClientPool(client_list)
            
            # 創建測試指令
            instruction = client_list[0].create_instruction(
                instruction_type='structured_output',
                description='測試客戶端池負載均衡',
                output_schema={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'provider': {'type': 'string'}
                    },
                    'required': ['message']
                }
            )
            
            # 執行多次請求測試負載均衡
            test_inputs = [f'測試請求 {i+1}' for i in range(5)]
            
            start_time = time.time()
            
            for test_input in test_inputs:
                response = pool.execute(instruction, test_input)
                
                if response['status'] != 'success':
                    print(f"❌ 客戶端池執行失敗: {response.get('errors', [])}")
                    return False
            
            end_time = time.time()
            pool_duration = end_time - start_time
            
            # 獲取池統計信息
            stats = pool.get_stats()
            
            print(f"✅ 客戶端池測試成功:")
            print(f"   - 總請求數: {stats['total_requests']}")
            print(f"   - 成功率: {stats['success_rate']:.2%}")
            print(f"   - 平均響應時間: {stats['avg_response_time']:.2f}秒")
            print(f"   - 總耗時: {pool_duration:.2f}秒")
            
            # 記錄性能指標
            self.results['performance_metrics']['client_pool'] = {
                'total_requests': stats['total_requests'],
                'success_rate': stats['success_rate'],
                'avg_response_time': stats['avg_response_time'],
                'total_time': pool_duration
            }
            
            return True
            
        except Exception as e:
            print(f"❌ 客戶端池測試異常: {e}")
            return False
    
    def test_health_checks(self) -> bool:
        """測試健康檢查"""
        for client_name, client in self.clients.items():
            try:
                health = client.health_check()
                
                if health['status'] == 'healthy':
                    print(f"✅ {client_name}: 健康檢查通過")
                else:
                    print(f"⚠️ {client_name}: 健康檢查警告 - {health.get('error', '未知錯誤')}")
                
                # 獲取客戶端統計信息
                stats = client.get_stats()
                print(f"   - 總請求數: {stats.get('total_requests', 0)}")
                print(f"   - 成功率: {stats.get('success_rate', 0):.2%}")
                
            except Exception as e:
                print(f"❌ {client_name}: 健康檢查異常 - {e}")
                return False
        
        return True
    
    def test_concurrent_processing(self) -> bool:
        """測試並發處理"""
        if not self.clients:
            return False
        
        # 選擇第一個可用客戶端
        client_name, client = next(iter(self.clients.items()))
        
        try:
            # 創建測試指令
            instruction = client.create_instruction(
                instruction_type='structured_output',
                description='測試並發處理',
                output_schema={
                    'type': 'object',
                    'properties': {
                        'result': {'type': 'string'},
                        'request_id': {'type': 'integer'}
                    },
                    'required': ['result']
                }
            )
            
            # 準備並發請求
            concurrent_requests = 5
            test_inputs = [f'並發請求 {i+1}' for i in range(concurrent_requests)]
            
            start_time = time.time()
            
            # 使用線程池執行並發請求
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(client.execute, instruction, test_input)
                    for test_input in test_inputs
                ]
                
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        results.append(result)
                    except Exception as e:
                        print(f"❌ 並發請求異常: {e}")
                        results.append({'status': 'error', 'errors': [str(e)]})
            
            end_time = time.time()
            concurrent_duration = end_time - start_time
            
            # 統計結果
            success_count = sum(1 for r in results if r['status'] == 'success')
            
            print(f"✅ {client_name}: 並發處理測試完成")
            print(f"   - 並發請求數: {concurrent_requests}")
            print(f"   - 成功請求數: {success_count}")
            print(f"   - 成功率: {success_count/concurrent_requests:.2%}")
            print(f"   - 總耗時: {concurrent_duration:.2f}秒")
            print(f"   - 平均每請求: {concurrent_duration/concurrent_requests:.2f}秒")
            
            # 記錄性能指標
            self.results['performance_metrics']['concurrent_processing'] = {
                'concurrent_requests': concurrent_requests,
                'successful_requests': success_count,
                'success_rate': success_count / concurrent_requests,
                'total_time': concurrent_duration,
                'avg_time_per_request': concurrent_duration / concurrent_requests
            }
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ 並發處理測試異常: {e}")
            return False
    
    def run_all_tests(self) -> None:
        """運行所有測試"""
        print("🚀 開始LLM標準庫集成測試")
        print("=" * 60)
        
        # 設置客戶端
        self._setup_clients()
        
        # 定義測試套件
        test_suite = [
            ('基本指令執行', self.test_basic_instruction_execution),
            ('結構化輸出驗證', self.test_structured_output_validation),
            ('批量處理', self.test_batch_processing),
            ('錯誤處理', self.test_error_handling),
            ('健康檢查', self.test_health_checks),
            ('並發處理', self.test_concurrent_processing),
            ('客戶端池', self.test_client_pool),
        ]
        
        # 運行測試
        for test_name, test_func in test_suite:
            self._run_test(test_name, test_func)
        
        # 輸出測試結果
        self._print_test_results()
    
    def _print_test_results(self) -> None:
        """輸出測試結果"""
        print("\n" + "=" * 60)
        print("📊 測試結果摘要")
        print("=" * 60)
        
        total = self.results['total_tests']
        passed = self.results['passed_tests']
        failed = self.results['failed_tests']
        
        print(f"總測試數: {total}")
        print(f"通過測試: {passed} ✅")
        print(f"失敗測試: {failed} ❌")
        print(f"成功率: {(passed/total*100) if total > 0 else 0:.1f}%")
        
        if self.results['errors']:
            print("\n❌ 錯誤詳情:")
            for error in self.results['errors']:
                print(f"   - {error}")
        
        if self.results['performance_metrics']:
            print("\n📈 性能指標:")
            for metric_name, metrics in self.results['performance_metrics'].items():
                print(f"\n{metric_name}:")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        print(f"   - {key}: {value:.3f}")
                    else:
                        print(f"   - {key}: {value}")
        
        # 保存結果到文件
        try:
            with open('test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print("\n💾 測試結果已保存到 test_results.json")
        except Exception as e:
            print(f"\n⚠️ 保存測試結果失敗: {e}")
        
        print("\n" + "=" * 60)
        if failed == 0:
            print("🎉 所有測試通過！LLM標準庫功能正常。")
        else:
            print(f"⚠️ 有 {failed} 個測試失敗，請檢查錯誤詳情。")
        print("=" * 60)


def main():
    """主函數"""
    print("LLM指令遵循與結構化輸出標準庫 - 集成測試")
    print("版本: 1.0.0")
    print("作者: JobSpy Team")
    print()
    
    # 檢查環境變量
    required_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'DEEPSEEK_API_KEY']
    available_vars = [var for var in required_vars if os.getenv(var)]
    
    if not available_vars:
        print("⚠️ 警告: 沒有設置任何API密鑰環境變量")
        print("請設置以下環境變量之一:")
        for var in required_vars:
            print(f"   - {var}")
        print("\n或者確保LiteLLM代理服務器正在運行 (http://localhost:4000)")
        print()
    else:
        print(f"✅ 檢測到 {len(available_vars)} 個API密鑰環境變量")
        print()
    
    # 運行測試
    tester = LLMStandardTester()
    tester.run_all_tests()


if __name__ == '__main__':
    main()