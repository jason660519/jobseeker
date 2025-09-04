"""高級使用示例"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm_standard import StandardLLMClient
from llm_standard.client import LLMClientPool


def example_client_pool():
    """客戶端池示例 - 負載均衡和故障轉移"""
    print("=== 客戶端池示例 ===")
    
    # 創建多個客戶端
    clients = [
        StandardLLMClient(
            provider="openai",
            api_key="your-openai-api-key",
            model="gpt-4"
        ),
        StandardLLMClient(
            provider="anthropic",
            api_key="your-anthropic-api-key",
            model="claude-3-haiku-20240307"
        ),
        StandardLLMClient(
            provider="deepseek",
            api_key="your-deepseek-api-key",
            model="deepseek-chat"
        )
    ]
    
    # 創建客戶端池
    pool = LLMClientPool(clients)
    
    # 創建測試指令
    instruction = {
        "instruction_type": "structured_output",
        "version": "1.0",
        "task": {
            "description": "分析產品評論的情感和評分"
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                "aspects": {
                    "type": "object",
                    "properties": {
                        "quality": {"type": "integer", "minimum": 1, "maximum": 5},
                        "price": {"type": "integer", "minimum": 1, "maximum": 5},
                        "service": {"type": "integer", "minimum": 1, "maximum": 5}
                    }
                }
            },
            "required": ["sentiment", "rating"]
        }
    }
    
    # 測試評論
    reviews = [
        "這個產品質量很好，價格合理，客服態度也不錯，推薦購買！",
        "產品一般般，價格偏高，不太值得。",
        "質量還可以，但是物流太慢了，等了一個星期才到。",
        "非常滿意！產品超出預期，客服響應及時，五星好評！",
        "產品有瑕疵，申請退款被拒絕，很失望。"
    ]
    
    print(f"使用客戶端池處理 {len(reviews)} 條評論...")
    
    # 使用客戶端池處理
    for i, review in enumerate(reviews):
        try:
            start_time = time.time()
            response = pool.execute(instruction, review)
            processing_time = time.time() - start_time
            
            if response['status'] == 'success':
                data = response['data']
                provider = response['model_info']['provider']
                print(f"\n評論 {i+1} (使用 {provider}):")
                print(f"  情感: {data['sentiment']}")
                print(f"  評分: {data['rating']}/5")
                if 'aspects' in data:
                    aspects = data['aspects']
                    print(f"  質量: {aspects.get('quality', 'N/A')}/5")
                    print(f"  價格: {aspects.get('price', 'N/A')}/5")
                    print(f"  服務: {aspects.get('service', 'N/A')}/5")
                print(f"  處理時間: {processing_time:.2f}秒")
            else:
                print(f"評論 {i+1} 處理失敗: {response['errors']}")
                
        except Exception as e:
            print(f"評論 {i+1} 錯誤: {e}")
    
    # 檢查所有客戶端健康狀態
    print("\n=== 客戶端健康檢查 ===")
    health_results = pool.health_check_all()
    for client_name, result in health_results.items():
        status_emoji = "✅" if result['status'] == 'healthy' else "❌"
        print(f"{status_emoji} {client_name}: {result['status']}")
        if result['status'] == 'healthy':
            print(f"   響應時間: {result.get('response_time', 'N/A'):.2f}秒")
        else:
            print(f"   錯誤: {result.get('error', 'N/A')}")


def example_concurrent_processing():
    """並發處理示例"""
    print("\n=== 並發處理示例 ===")
    
    client = StandardLLMClient(
        provider="openai",
        api_key="your-openai-api-key",
        model="gpt-3.5-turbo"
    )
    
    # 創建文本摘要指令
    instruction = {
        "instruction_type": "summarization",
        "version": "1.0",
        "task": {
            "description": "生成文章摘要",
            "constraints": ["max_length: 100", "language: zh-CN"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "文章摘要"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "關鍵要點"
                },
                "word_count": {"type": "integer", "description": "摘要字數"}
            },
            "required": ["summary", "key_points", "word_count"]
        }
    }
    
    # 模擬多篇文章
    articles = [
        "人工智能技術在近年來取得了突破性進展，特別是在自然語言處理、計算機視覺和機器學習領域。深度學習算法的發展使得AI系統能夠處理更複雜的任務，從語音識別到圖像分析，再到自動駕駛汽車。然而，AI技術的快速發展也帶來了倫理和安全方面的挑戰，需要制定相應的規範和標準。",
        "區塊鏈技術作為一種分布式賬本技術，正在改變金融、供應鏈管理和數據安全等多個行業。其去中心化的特性提供了更高的透明度和安全性，但同時也面臨著可擴展性和能源消耗的挑戰。隨著技術的成熟，我們看到越來越多的企業開始採用區塊鏈解決方案。",
        "雲計算已經成為現代企業IT基礎設施的核心組成部分。它提供了彈性、可擴展性和成本效益，使企業能夠快速響應市場變化。混合雲和多雲策略正在成為主流，企業可以根據具體需求選擇最適合的雲服務提供商和部署模式。",
        "物聯網(IoT)設備的普及正在創造一個高度互聯的世界。從智能家居到工業4.0，IoT技術正在改變我們的生活和工作方式。然而，大量設備的連接也帶來了數據隱私和網絡安全的新挑戰，需要更強大的安全框架和協議。",
        "5G網絡的部署為移動通信帶來了革命性的改變，提供了更高的速度、更低的延遲和更大的連接密度。這為增強現實、虛擬現實、自動駕駛和遠程醫療等應用提供了技術基礎。5G技術的普及將推動新一輪的數字化轉型。"
    ]
    
    def process_article(article_text, article_id):
        """處理單篇文章"""
        try:
            start_time = time.time()
            response = client.execute(instruction, article_text)
            processing_time = time.time() - start_time
            
            return {
                'id': article_id,
                'success': True,
                'response': response,
                'processing_time': processing_time
            }
        except Exception as e:
            return {
                'id': article_id,
                'success': False,
                'error': str(e),
                'processing_time': 0
            }
    
    # 並發處理
    print(f"並發處理 {len(articles)} 篇文章...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任務
        future_to_id = {
            executor.submit(process_article, article, i): i 
            for i, article in enumerate(articles)
        }
        
        # 收集結果
        results = []
        for future in as_completed(future_to_id):
            result = future.result()
            results.append(result)
    
    total_time = time.time() - start_time
    
    # 按ID排序結果
    results.sort(key=lambda x: x['id'])
    
    # 顯示結果
    successful_count = 0
    total_processing_time = 0
    
    for result in results:
        article_id = result['id']
        if result['success']:
            successful_count += 1
            total_processing_time += result['processing_time']
            
            response = result['response']
            if response['status'] == 'success':
                data = response['data']
                print(f"\n文章 {article_id + 1}:")
                print(f"  摘要: {data['summary']}")
                print(f"  關鍵要點: {', '.join(data['key_points'])}")
                print(f"  字數: {data['word_count']}")
                print(f"  處理時間: {result['processing_time']:.2f}秒")
            else:
                print(f"文章 {article_id + 1} 處理失敗: {response['errors']}")
        else:
            print(f"文章 {article_id + 1} 錯誤: {result['error']}")
    
    print(f"\n=== 並發處理統計 ===")
    print(f"總耗時: {total_time:.2f}秒")
    print(f"成功處理: {successful_count}/{len(articles)}")
    print(f"平均處理時間: {total_processing_time/successful_count:.2f}秒" if successful_count > 0 else "N/A")
    print(f"並發效率: {(total_processing_time/total_time)*100:.1f}%" if total_time > 0 else "N/A")


def example_custom_validation():
    """自定義驗證示例"""
    print("\n=== 自定義驗證示例 ===")
    
    client = StandardLLMClient(
        provider="anthropic",
        api_key="your-anthropic-api-key",
        model="claude-3-haiku-20240307",
        validate_instructions=True,
        validate_responses=True
    )
    
    # 創建複雜的Schema
    instruction = {
        "instruction_type": "extraction",
        "version": "1.0",
        "task": {
            "description": "從招聘信息中提取結構化數據",
            "context": "這是一個招聘網站的職位描述",
            "constraints": [
                "output_language: zh-CN",
                "format: json_only",
                "validation: strict",
                "encoding: utf-8"
            ]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "職位名稱"},
                "company": {"type": "string", "description": "公司名稱"},
                "location": {"type": "string", "description": "工作地點"},
                "salary_range": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "integer", "minimum": 0},
                        "max": {"type": "integer", "minimum": 0},
                        "currency": {"type": "string", "default": "CNY"}
                    },
                    "required": ["min", "max"]
                },
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "職位要求"
                },
                "benefits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "福利待遇"
                },
                "experience_years": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 50,
                    "description": "所需工作經驗年數"
                },
                "education": {
                    "type": "string",
                    "enum": ["高中", "大專", "本科", "碩士", "博士", "不限"],
                    "description": "學歷要求"
                },
                "job_type": {
                    "type": "string",
                    "enum": ["全職", "兼職", "實習", "合同工"],
                    "description": "工作類型"
                },
                "contact_info": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "phone": {"type": "string", "format": "phone-number"},
                        "hr_name": {"type": "string"}
                    }
                }
            },
            "required": ["job_title", "company", "location", "requirements", "experience_years", "education", "job_type"]
        },
        "examples": [
            {
                "input": "高級Python開發工程師 - ABC科技有限公司，北京，薪資15-25K，要求3年以上經驗，本科學歷",
                "output": {
                    "job_title": "高級Python開發工程師",
                    "company": "ABC科技有限公司",
                    "location": "北京",
                    "salary_range": {"min": 15000, "max": 25000, "currency": "CNY"},
                    "experience_years": 3,
                    "education": "本科",
                    "job_type": "全職"
                }
            }
        ],
        "metadata": {
            "priority": "high",
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    # 測試招聘信息
    job_posting = """
    【職位】資深前端開發工程師
    【公司】XYZ互聯網科技有限公司
    【地點】上海市浦東新區
    【薪資】20K-35K·14薪
    【經驗】5年以上前端開發經驗
    【學歷】本科及以上學歷，計算機相關專業優先
    【類型】全職
    
    【職位要求】
    1. 精通JavaScript、HTML5、CSS3
    2. 熟練使用React、Vue等前端框架
    3. 有移動端開發經驗
    4. 熟悉前端工程化工具
    5. 良好的代碼規範和團隊協作能力
    
    【福利待遇】
    - 五險一金
    - 年終獎金
    - 帶薪年假
    - 技能培訓
    - 彈性工作時間
    
    【聯繫方式】
    HR：李小姐
    郵箱：hr@xyz.com
    電話：021-12345678
    """
    
    try:
        print("處理招聘信息...")
        start_time = time.time()
        response = client.execute(instruction, job_posting)
        processing_time = time.time() - start_time
        
        if response['status'] == 'success':
            data = response['data']
            print("\n提取結果:")
            print(f"  職位: {data['job_title']}")
            print(f"  公司: {data['company']}")
            print(f"  地點: {data['location']}")
            
            if 'salary_range' in data:
                salary = data['salary_range']
                print(f"  薪資: {salary['min']}-{salary['max']} {salary.get('currency', 'CNY')}")
            
            print(f"  經驗要求: {data['experience_years']}年")
            print(f"  學歷要求: {data['education']}")
            print(f"  工作類型: {data['job_type']}")
            
            if 'requirements' in data:
                print(f"  職位要求: {', '.join(data['requirements'][:3])}...")
            
            if 'benefits' in data:
                print(f"  福利待遇: {', '.join(data['benefits'][:3])}...")
            
            if 'contact_info' in data:
                contact = data['contact_info']
                print(f"  聯繫人: {contact.get('hr_name', 'N/A')}")
                print(f"  郵箱: {contact.get('email', 'N/A')}")
                print(f"  電話: {contact.get('phone', 'N/A')}")
            
            print(f"\n處理時間: {processing_time:.2f}秒")
            print(f"Token使用: {response['metadata']['token_usage']['total_tokens']}")
            
            # 檢查警告
            if response.get('warnings'):
                print("\n警告信息:")
                for warning in response['warnings']:
                    print(f"  - {warning['message']}")
        
        else:
            print(f"處理失敗: {response['errors']}")
            
    except Exception as e:
        print(f"錯誤: {e}")
        if hasattr(e, 'error_code'):
            print(f"錯誤代碼: {e.error_code}")


def example_performance_monitoring():
    """性能監控示例"""
    print("\n=== 性能監控示例 ===")
    
    client = StandardLLMClient(
        provider="deepseek",
        api_key="your-deepseek-api-key",
        model="deepseek-chat"
    )
    
    # 創建簡單的測試指令
    instruction = client.create_instruction(
        instruction_type="text_generation",
        description="生成產品描述",
        output_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "features": {"type": "array", "items": {"type": "string"}},
                "price_range": {"type": "string"}
            },
            "required": ["title", "description"]
        }
    )
    
    # 性能測試
    test_inputs = [
        "智能手機",
        "筆記本電腦",
        "無線耳機",
        "智能手錶",
        "平板電腦"
    ]
    
    print(f"執行 {len(test_inputs)} 次性能測試...")
    
    results = []
    total_start_time = time.time()
    
    for i, test_input in enumerate(test_inputs):
        try:
            start_time = time.time()
            response = client.execute(instruction, f"為{test_input}生成產品描述")
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            result = {
                'test_id': i + 1,
                'input': test_input,
                'success': response['status'] == 'success',
                'processing_time': processing_time,
                'token_usage': response['metadata']['token_usage'],
                'confidence_score': response['metadata'].get('confidence_score', 0)
            }
            
            results.append(result)
            
            print(f"測試 {i+1}: {test_input} - {processing_time:.2f}秒 - {'✅' if result['success'] else '❌'}")
            
        except Exception as e:
            result = {
                'test_id': i + 1,
                'input': test_input,
                'success': False,
                'processing_time': 0,
                'error': str(e)
            }
            results.append(result)
            print(f"測試 {i+1}: {test_input} - 錯誤: {e}")
    
    total_time = time.time() - total_start_time
    
    # 統計分析
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        processing_times = [r['processing_time'] for r in successful_results]
        token_counts = [r['token_usage']['total_tokens'] for r in successful_results]
        confidence_scores = [r['confidence_score'] for r in successful_results]
        
        print(f"\n=== 性能統計 ===")
        print(f"總測試數: {len(results)}")
        print(f"成功數: {len(successful_results)}")
        print(f"成功率: {len(successful_results)/len(results)*100:.1f}%")
        print(f"總耗時: {total_time:.2f}秒")
        print(f"\n響應時間統計:")
        print(f"  平均: {sum(processing_times)/len(processing_times):.2f}秒")
        print(f"  最快: {min(processing_times):.2f}秒")
        print(f"  最慢: {max(processing_times):.2f}秒")
        print(f"\nToken使用統計:")
        print(f"  平均: {sum(token_counts)/len(token_counts):.0f}")
        print(f"  最少: {min(token_counts)}")
        print(f"  最多: {max(token_counts)}")
        print(f"  總計: {sum(token_counts)}")
        print(f"\n置信度統計:")
        print(f"  平均: {sum(confidence_scores)/len(confidence_scores):.2f}")
        print(f"  最低: {min(confidence_scores):.2f}")
        print(f"  最高: {max(confidence_scores):.2f}")
    else:
        print("\n所有測試都失敗了！")


if __name__ == "__main__":
    print("LLM指令遵循與結構化輸出標準庫 - 高級使用示例")
    print("=" * 60)
    
    # 注意：運行前請設置正確的API密鑰
    print("注意：請在代碼中設置正確的API密鑰後運行示例")
    
    # example_client_pool()
    # example_concurrent_processing()
    # example_custom_validation()
    # example_performance_monitoring()
    
    print("\n所有高級示例完成！")