#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版LLM模型比較測試
擴充更多測試案例，比較不同LLM模型的輸出表現差異

功能特色：
1. 支援多個LLM提供商的並行測試
2. 詳細的性能指標分析
3. 模型一致性評估
4. 邊界案例和複雜場景測試
5. 生成詳細的比較報告

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from jobseeker.llm_config import LLMConfigManager


@dataclass
class TestCase:
    """測試案例數據結構"""
    id: str
    category: str
    subcategory: str
    description: str
    query: str
    expected_job_related: bool
    difficulty_level: str  # easy, medium, hard, extreme
    language: str  # zh, en, mixed
    context_type: str  # explicit, implicit, ambiguous
    expected_confidence_range: Tuple[float, float]  # (min, max)
    tags: List[str]


@dataclass
class ModelTestResult:
    """單個模型測試結果"""
    provider: str
    model_name: str
    test_id: str
    query: str
    expected: bool
    actual: bool
    confidence: float
    response_time: float
    passed: bool
    intent_type: str
    reasoning: str
    structured_intent: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ModelPerformanceMetrics:
    """模型性能指標"""
    provider: str
    model_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    accuracy: float
    avg_confidence: float
    avg_response_time: float
    consistency_score: float
    category_performance: Dict[str, float]
    difficulty_performance: Dict[str, float]
    language_performance: Dict[str, float]
    error_rate: float
    edge_case_handling: float


class EnhancedLLMModelComparisonTester:
    """增強版LLM模型比較測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.config_manager = LLMConfigManager()
        self.test_cases = self._create_comprehensive_test_cases()
        self.results: Dict[str, List[ModelTestResult]] = {}
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        
    def _create_comprehensive_test_cases(self) -> List[TestCase]:
        """創建全面的測試案例"""
        test_cases = []
        
        # 1. 基礎求職查詢 (Easy)
        basic_job_queries = [
            TestCase(
                id="basic_001",
                category="基礎求職查詢",
                subcategory="職位+地點",
                description="標準職位搜尋",
                query="Python工程師 台北",
                expected_job_related=True,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.8, 1.0),
                tags=["職位", "地點", "程式語言"]
            ),
            TestCase(
                id="basic_002",
                category="基礎求職查詢",
                subcategory="職位+地點",
                description="英文職位搜尋",
                query="Software Engineer in Taipei",
                expected_job_related=True,
                difficulty_level="easy",
                language="en",
                context_type="explicit",
                expected_confidence_range=(0.8, 1.0),
                tags=["職位", "地點", "英文"]
            ),
            TestCase(
                id="basic_003",
                category="基礎求職查詢",
                subcategory="職位+薪資",
                description="包含薪資要求",
                query="前端工程師 月薪60k以上",
                expected_job_related=True,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.7, 1.0),
                tags=["職位", "薪資", "前端"]
            ),
            TestCase(
                id="basic_004",
                category="基礎求職查詢",
                subcategory="技能導向",
                description="技能關鍵字搜尋",
                query="React開發者 遠程工作",
                expected_job_related=True,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.7, 1.0),
                tags=["技能", "遠程", "框架"]
            ),
            TestCase(
                id="basic_005",
                category="基礎求職查詢",
                subcategory="多技能組合",
                description="多個技能組合",
                query="Python Django PostgreSQL 後端開發",
                expected_job_related=True,
                difficulty_level="medium",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.6, 0.9),
                tags=["多技能", "後端", "資料庫"]
            )
        ]
        
        # 2. 進階求職查詢 (Medium)
        advanced_job_queries = [
            TestCase(
                id="advanced_001",
                category="進階求職查詢",
                subcategory="複合條件",
                description="多重條件組合",
                query="尋找台北的全端工程師職位，要求React和Node.js經驗，薪資50k以上，可遠程工作",
                expected_job_related=True,
                difficulty_level="medium",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.7, 0.9),
                tags=["複合條件", "全端", "遠程", "薪資"]
            ),
            TestCase(
                id="advanced_002",
                category="進階求職查詢",
                subcategory="職涯發展",
                description="職涯轉換諮詢",
                query="從傳統製造業轉入科技業的軟體工程師職位建議",
                expected_job_related=True,
                difficulty_level="medium",
                language="zh",
                context_type="implicit",
                expected_confidence_range=(0.6, 0.8),
                tags=["職涯轉換", "諮詢", "製造業", "科技業"]
            ),
            TestCase(
                id="advanced_003",
                category="進階求職查詢",
                subcategory="新興技術",
                description="AI/ML相關職位",
                query="機器學習工程師 TensorFlow PyTorch 深度學習 新竹科學園區",
                expected_job_related=True,
                difficulty_level="medium",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.7, 0.9),
                tags=["AI", "ML", "深度學習", "科學園區"]
            ),
            TestCase(
                id="advanced_004",
                category="進階求職查詢",
                subcategory="國際化",
                description="跨國公司職位",
                query="Looking for DevOps engineer position in multinational company, AWS experience required, Taipei or remote",
                expected_job_related=True,
                difficulty_level="medium",
                language="en",
                context_type="explicit",
                expected_confidence_range=(0.7, 0.9),
                tags=["DevOps", "跨國", "AWS", "雲端"]
            ),
            TestCase(
                id="advanced_005",
                category="進階求職查詢",
                subcategory="創業相關",
                description="新創公司職位",
                query="想加入新創公司擔任產品經理，有電商背景，希望在台北",
                expected_job_related=True,
                difficulty_level="medium",
                language="zh",
                context_type="implicit",
                expected_confidence_range=(0.6, 0.8),
                tags=["新創", "產品經理", "電商"]
            )
        ]
        
        # 3. 困難邊界案例 (Hard)
        edge_cases = [
            TestCase(
                id="edge_001",
                category="邊界案例",
                subcategory="模糊意圖",
                description="僅地點名稱",
                query="台北",
                expected_job_related=False,
                difficulty_level="hard",
                language="zh",
                context_type="ambiguous",
                expected_confidence_range=(0.0, 0.3),
                tags=["地點", "模糊"]
            ),
            TestCase(
                id="edge_002",
                category="邊界案例",
                subcategory="學習意圖",
                description="技能學習查詢",
                query="如何學習Python程式設計的最佳方法和資源推薦",
                expected_job_related=False,
                difficulty_level="hard",
                language="zh",
                context_type="ambiguous",
                expected_confidence_range=(0.0, 0.4),
                tags=["學習", "教育", "資源"]
            ),
            TestCase(
                id="edge_003",
                category="邊界案例",
                subcategory="薪資討論",
                description="純薪資討論",
                query="軟體工程師的薪水水準如何",
                expected_job_related=False,
                difficulty_level="hard",
                language="zh",
                context_type="ambiguous",
                expected_confidence_range=(0.2, 0.6),
                tags=["薪資", "討論", "市場"]
            ),
            TestCase(
                id="edge_004",
                category="邊界案例",
                subcategory="技術討論",
                description="純技術討論",
                query="React和Vue.js的優缺點比較",
                expected_job_related=False,
                difficulty_level="hard",
                language="zh",
                context_type="ambiguous",
                expected_confidence_range=(0.0, 0.4),
                tags=["技術", "比較", "框架"]
            ),
            TestCase(
                id="edge_005",
                category="邊界案例",
                subcategory="混合語言",
                description="中英混合查詢",
                query="想找Software Engineer的工作在台北，需要會Python和JavaScript",
                expected_job_related=True,
                difficulty_level="hard",
                language="mixed",
                context_type="explicit",
                expected_confidence_range=(0.6, 0.8),
                tags=["混合語言", "職位", "技能"]
            )
        ]
        
        # 4. 極端測試案例 (Extreme)
        extreme_cases = [
            TestCase(
                id="extreme_001",
                category="極端案例",
                subcategory="超長查詢",
                description="非常詳細的求職需求",
                query="我是一個有5年經驗的全端工程師，熟悉React、Vue.js、Node.js、Python、Django、PostgreSQL、MongoDB、AWS、Docker、Kubernetes，目前在一家傳統金融公司工作，想轉到新創科技公司，希望能找到台北或新竹的遠程工作機會，薪資期望在80k-120k之間，公司文化要開放創新，有學習成長機會，最好是B2C產品導向的公司",
                expected_job_related=True,
                difficulty_level="extreme",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.8, 1.0),
                tags=["超長", "詳細", "多技能", "轉職"]
            ),
            TestCase(
                id="extreme_002",
                category="極端案例",
                subcategory="隱含意圖",
                description="高度隱含的求職意圖",
                query="最近工作壓力很大，想換個環境，聽說科技業待遇不錯",
                expected_job_related=True,
                difficulty_level="extreme",
                language="zh",
                context_type="implicit",
                expected_confidence_range=(0.3, 0.7),
                tags=["隱含", "轉職", "壓力"]
            ),
            TestCase(
                id="extreme_003",
                category="極端案例",
                subcategory="反向查詢",
                description="不想要的職位類型",
                query="不想做前端開發，也不想加班太多，有什麼其他的工程師職位推薦",
                expected_job_related=True,
                difficulty_level="extreme",
                language="zh",
                context_type="implicit",
                expected_confidence_range=(0.4, 0.7),
                tags=["反向", "排除", "推薦"]
            ),
            TestCase(
                id="extreme_004",
                category="極端案例",
                subcategory="情境化查詢",
                description="特定情境下的求職",
                query="剛畢業的資工系學生，沒有實習經驗，但有做過一些side project，想找entry level的工作",
                expected_job_related=True,
                difficulty_level="extreme",
                language="zh",
                context_type="implicit",
                expected_confidence_range=(0.6, 0.8),
                tags=["新鮮人", "無經驗", "side project"]
            ),
            TestCase(
                id="extreme_005",
                category="極端案例",
                subcategory="多重否定",
                description="複雜的否定表達",
                query="不是不想找工作，只是不確定現在的市場環境適不適合轉職",
                expected_job_related=True,
                difficulty_level="extreme",
                language="zh",
                context_type="ambiguous",
                expected_confidence_range=(0.2, 0.6),
                tags=["多重否定", "不確定", "市場"]
            )
        ]
        
        # 5. 非求職相關查詢
        non_job_queries = [
            TestCase(
                id="non_job_001",
                category="非求職相關",
                subcategory="天氣查詢",
                description="天氣資訊",
                query="今天台北的天氣如何",
                expected_job_related=False,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.0, 0.2),
                tags=["天氣", "資訊"]
            ),
            TestCase(
                id="non_job_002",
                category="非求職相關",
                subcategory="娛樂推薦",
                description="電影推薦",
                query="推薦一些好看的科幻電影",
                expected_job_related=False,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.0, 0.2),
                tags=["娛樂", "電影"]
            ),
            TestCase(
                id="non_job_003",
                category="非求職相關",
                subcategory="購物查詢",
                description="商品購買",
                query="哪裡可以買到便宜的MacBook Pro",
                expected_job_related=False,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.0, 0.2),
                tags=["購物", "電腦"]
            ),
            TestCase(
                id="non_job_004",
                category="非求職相關",
                subcategory="旅遊規劃",
                description="旅遊景點",
                query="台北有什麼好玩的景點和美食推薦",
                expected_job_related=False,
                difficulty_level="medium",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.0, 0.3),
                tags=["旅遊", "景點", "美食"]
            ),
            TestCase(
                id="non_job_005",
                category="非求職相關",
                subcategory="健康諮詢",
                description="健康問題",
                query="最近常常頭痛，可能是什麼原因",
                expected_job_related=False,
                difficulty_level="easy",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.0, 0.2),
                tags=["健康", "醫療"]
            )
        ]
        
        # 6. 特殊語言和格式測試
        special_format_tests = [
            TestCase(
                id="special_001",
                category="特殊格式",
                subcategory="表情符號",
                description="包含表情符號",
                query="找工作好難😭 有沒有適合新手的程式設計師職位🤔",
                expected_job_related=True,
                difficulty_level="medium",
                language="zh",
                context_type="explicit",
                expected_confidence_range=(0.6, 0.8),
                tags=["表情符號", "新手"]
            ),
            TestCase(
                id="special_002",
                category="特殊格式",
                subcategory="縮寫術語",
                description="技術縮寫",
                query="找ML/AI相關的SWE職位，prefer FAANG或unicorn startup",
                expected_job_related=True,
                difficulty_level="hard",
                language="mixed",
                context_type="explicit",
                expected_confidence_range=(0.6, 0.8),
                tags=["縮寫", "術語", "FAANG"]
            ),
            TestCase(
                id="special_003",
                category="特殊格式",
                subcategory="數字符號",
                description="包含特殊符號",
                query="C++ / C# 開發者 @ 台北，薪資 > 70K",
                expected_job_related=True,
                difficulty_level="medium",
                language="mixed",
                context_type="explicit",
                expected_confidence_range=(0.7, 0.9),
                tags=["符號", "程式語言"]
            )
        ]
        
        # 合併所有測試案例
        all_test_cases = (
            basic_job_queries + 
            advanced_job_queries + 
            edge_cases + 
            extreme_cases + 
            non_job_queries + 
            special_format_tests
        )
        
        return all_test_cases
    
    def run_model_comparison_test(self, providers: Optional[List[LLMProvider]] = None) -> Dict[str, Any]:
        """運行模型比較測試"""
        print("🚀 開始增強版LLM模型比較測試")
        print("=" * 60)
        
        # 確定要測試的提供商
        if providers is None:
            providers = self.config_manager.get_available_providers()
        
        if not providers:
            print("❌ 沒有可用的LLM提供商")
            return {}
        
        print(f"📋 測試提供商: {[p.value for p in providers]}")
        print(f"📊 測試案例數量: {len(self.test_cases)}")
        print()
        
        # 為每個提供商運行測試
        for provider in providers:
            print(f"\n🔄 測試提供商: {provider.value}")
            print("-" * 40)
            
            try:
                analyzer = LLMIntentAnalyzer(provider=provider)
                model_name = self.config_manager.get_config(provider).model_name or "default"
                
                provider_results = []
                
                for i, test_case in enumerate(self.test_cases, 1):
                    print(f"\r進度: {i}/{len(self.test_cases)} ({i/len(self.test_cases)*100:.1f}%)", end="", flush=True)
                    
                    # 執行單個測試
                    result = self._run_single_test(analyzer, test_case, provider.value, model_name)
                    provider_results.append(result)
                
                print()  # 換行
                self.results[provider.value] = provider_results
                
                # 計算性能指標
                metrics = self._calculate_performance_metrics(provider.value, model_name, provider_results)
                self.performance_metrics[provider.value] = metrics
                
                print(f"✅ {provider.value} 測試完成")
                print(f"   準確率: {metrics.accuracy:.1f}%")
                print(f"   平均響應時間: {metrics.avg_response_time:.2f}s")
                print(f"   錯誤率: {metrics.error_rate:.1f}%")
                
            except Exception as e:
                print(f"❌ {provider.value} 測試失敗: {str(e)}")
                continue
        
        # 生成比較報告
        comparison_report = self._generate_comparison_report()
        
        # 保存結果
        self._save_results(comparison_report)
        
        return comparison_report
    
    def _run_single_test(self, analyzer: LLMIntentAnalyzer, test_case: TestCase, 
                        provider: str, model_name: str) -> ModelTestResult:
        """運行單個測試案例"""
        start_time = time.time()
        
        try:
            # 執行意圖分析
            result = analyzer.analyze_intent(test_case.query)
            
            response_time = time.time() - start_time
            
            # 檢查結果
            actual_job_related = result.is_job_related
            passed = actual_job_related == test_case.expected_job_related
            
            # 提取結構化意圖
            structured_intent = {}
            if result.structured_intent and result.is_job_related:
                intent = result.structured_intent
                structured_intent = {
                    "job_titles": getattr(intent, 'job_titles', []),
                    "skills": getattr(intent, 'skills', []),
                    "locations": getattr(intent, 'locations', []),
                    "salary_range": getattr(intent, 'salary_range', None),
                    "work_type": getattr(intent, 'work_type', None)
                }
            
            return ModelTestResult(
                provider=provider,
                model_name=model_name,
                test_id=test_case.id,
                query=test_case.query,
                expected=test_case.expected_job_related,
                actual=actual_job_related,
                confidence=result.confidence,
                response_time=response_time,
                passed=passed,
                intent_type=result.intent_type.value if hasattr(result.intent_type, 'value') else str(result.intent_type),
                reasoning=getattr(result, 'llm_reasoning', ''),
                structured_intent=structured_intent
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ModelTestResult(
                provider=provider,
                model_name=model_name,
                test_id=test_case.id,
                query=test_case.query,
                expected=test_case.expected_job_related,
                actual=False,
                confidence=0.0,
                response_time=response_time,
                passed=False,
                intent_type="error",
                reasoning="",
                structured_intent={},
                error=str(e)
            )
    
    def _calculate_performance_metrics(self, provider: str, model_name: str, 
                                     results: List[ModelTestResult]) -> ModelPerformanceMetrics:
        """計算性能指標"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests
        accuracy = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # 計算平均置信度和響應時間
        valid_results = [r for r in results if r.error is None]
        avg_confidence = statistics.mean([r.confidence for r in valid_results]) if valid_results else 0
        avg_response_time = statistics.mean([r.response_time for r in results])
        
        # 錯誤率
        error_count = sum(1 for r in results if r.error is not None)
        error_rate = (error_count / total_tests) * 100 if total_tests > 0 else 0
        
        # 按類別計算性能
        category_performance = self._calculate_category_performance(results)
        
        # 按難度計算性能
        difficulty_performance = self._calculate_difficulty_performance(results)
        
        # 按語言計算性能
        language_performance = self._calculate_language_performance(results)
        
        # 計算一致性分數（置信度與實際結果的一致性）
        consistency_score = self._calculate_consistency_score(results)
        
        # 邊界案例處理能力
        edge_case_handling = self._calculate_edge_case_handling(results)
        
        return ModelPerformanceMetrics(
            provider=provider,
            model_name=model_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            accuracy=accuracy,
            avg_confidence=avg_confidence,
            avg_response_time=avg_response_time,
            consistency_score=consistency_score,
            category_performance=category_performance,
            difficulty_performance=difficulty_performance,
            language_performance=language_performance,
            error_rate=error_rate,
            edge_case_handling=edge_case_handling
        )
    
    def _calculate_category_performance(self, results: List[ModelTestResult]) -> Dict[str, float]:
        """計算各類別性能"""
        category_stats = {}
        
        for result in results:
            test_case = next((tc for tc in self.test_cases if tc.id == result.test_id), None)
            if test_case:
                category = test_case.category
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'passed': 0}
                
                category_stats[category]['total'] += 1
                if result.passed:
                    category_stats[category]['passed'] += 1
        
        return {
            category: (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            for category, stats in category_stats.items()
        }
    
    def _calculate_difficulty_performance(self, results: List[ModelTestResult]) -> Dict[str, float]:
        """計算各難度級別性能"""
        difficulty_stats = {}
        
        for result in results:
            test_case = next((tc for tc in self.test_cases if tc.id == result.test_id), None)
            if test_case:
                difficulty = test_case.difficulty_level
                if difficulty not in difficulty_stats:
                    difficulty_stats[difficulty] = {'total': 0, 'passed': 0}
                
                difficulty_stats[difficulty]['total'] += 1
                if result.passed:
                    difficulty_stats[difficulty]['passed'] += 1
        
        return {
            difficulty: (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            for difficulty, stats in difficulty_stats.items()
        }
    
    def _calculate_language_performance(self, results: List[ModelTestResult]) -> Dict[str, float]:
        """計算各語言性能"""
        language_stats = {}
        
        for result in results:
            test_case = next((tc for tc in self.test_cases if tc.id == result.test_id), None)
            if test_case:
                language = test_case.language
                if language not in language_stats:
                    language_stats[language] = {'total': 0, 'passed': 0}
                
                language_stats[language]['total'] += 1
                if result.passed:
                    language_stats[language]['passed'] += 1
        
        return {
            language: (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            for language, stats in language_stats.items()
        }
    
    def _calculate_consistency_score(self, results: List[ModelTestResult]) -> float:
        """計算一致性分數（置信度與結果的一致性）"""
        valid_results = [r for r in results if r.error is None]
        if not valid_results:
            return 0.0
        
        consistency_scores = []
        for result in valid_results:
            # 如果預測正確且置信度高，或預測錯誤且置信度低，則一致性高
            if result.passed:
                consistency = result.confidence
            else:
                consistency = 1.0 - result.confidence
            
            consistency_scores.append(consistency)
        
        return statistics.mean(consistency_scores) * 100
    
    def _calculate_edge_case_handling(self, results: List[ModelTestResult]) -> float:
        """計算邊界案例處理能力"""
        edge_case_results = []
        
        for result in results:
            test_case = next((tc for tc in self.test_cases if tc.id == result.test_id), None)
            if test_case and test_case.category == "邊界案例":
                edge_case_results.append(result)
        
        if not edge_case_results:
            return 0.0
        
        passed_edge_cases = sum(1 for r in edge_case_results if r.passed)
        return (passed_edge_cases / len(edge_case_results)) * 100
    
    def _generate_comparison_report(self) -> Dict[str, Any]:
        """生成比較報告"""
        if not self.performance_metrics:
            return {}
        
        # 整體統計
        providers = list(self.performance_metrics.keys())
        
        # 找出最佳表現的模型
        best_accuracy = max(self.performance_metrics.values(), key=lambda x: x.accuracy)
        best_speed = min(self.performance_metrics.values(), key=lambda x: x.avg_response_time)
        best_consistency = max(self.performance_metrics.values(), key=lambda x: x.consistency_score)
        best_edge_case = max(self.performance_metrics.values(), key=lambda x: x.edge_case_handling)
        
        # 計算平均指標
        avg_accuracy = statistics.mean([m.accuracy for m in self.performance_metrics.values()])
        avg_response_time = statistics.mean([m.avg_response_time for m in self.performance_metrics.values()])
        avg_consistency = statistics.mean([m.consistency_score for m in self.performance_metrics.values()])
        
        # 生成詳細比較
        detailed_comparison = self._generate_detailed_comparison()
        
        return {
            "test_summary": {
                "total_providers": len(providers),
                "total_test_cases": len(self.test_cases),
                "test_categories": list(set(tc.category for tc in self.test_cases)),
                "difficulty_levels": list(set(tc.difficulty_level for tc in self.test_cases)),
                "languages": list(set(tc.language for tc in self.test_cases)),
                "timestamp": datetime.now().isoformat()
            },
            "performance_summary": {
                "average_accuracy": avg_accuracy,
                "average_response_time": avg_response_time,
                "average_consistency": avg_consistency,
                "best_accuracy_model": {
                    "provider": best_accuracy.provider,
                    "accuracy": best_accuracy.accuracy
                },
                "fastest_model": {
                    "provider": best_speed.provider,
                    "response_time": best_speed.avg_response_time
                },
                "most_consistent_model": {
                    "provider": best_consistency.provider,
                    "consistency_score": best_consistency.consistency_score
                },
                "best_edge_case_model": {
                    "provider": best_edge_case.provider,
                    "edge_case_score": best_edge_case.edge_case_handling
                }
            },
            "detailed_metrics": {
                provider: asdict(metrics) for provider, metrics in self.performance_metrics.items()
            },
            "detailed_comparison": detailed_comparison,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_detailed_comparison(self) -> Dict[str, Any]:
        """生成詳細比較分析"""
        comparison = {
            "accuracy_ranking": [],
            "speed_ranking": [],
            "consistency_ranking": [],
            "category_comparison": {},
            "difficulty_comparison": {},
            "language_comparison": {}
        }
        
        # 準確率排名
        accuracy_sorted = sorted(self.performance_metrics.items(), 
                                key=lambda x: x[1].accuracy, reverse=True)
        comparison["accuracy_ranking"] = [
            {"provider": provider, "accuracy": metrics.accuracy}
            for provider, metrics in accuracy_sorted
        ]
        
        # 速度排名
        speed_sorted = sorted(self.performance_metrics.items(), 
                             key=lambda x: x[1].avg_response_time)
        comparison["speed_ranking"] = [
            {"provider": provider, "response_time": metrics.avg_response_time}
            for provider, metrics in speed_sorted
        ]
        
        # 一致性排名
        consistency_sorted = sorted(self.performance_metrics.items(), 
                                   key=lambda x: x[1].consistency_score, reverse=True)
        comparison["consistency_ranking"] = [
            {"provider": provider, "consistency_score": metrics.consistency_score}
            for provider, metrics in consistency_sorted
        ]
        
        # 類別比較
        all_categories = set()
        for metrics in self.performance_metrics.values():
            all_categories.update(metrics.category_performance.keys())
        
        for category in all_categories:
            comparison["category_comparison"][category] = {
                provider: metrics.category_performance.get(category, 0)
                for provider, metrics in self.performance_metrics.items()
            }
        
        # 難度比較
        all_difficulties = set()
        for metrics in self.performance_metrics.values():
            all_difficulties.update(metrics.difficulty_performance.keys())
        
        for difficulty in all_difficulties:
            comparison["difficulty_comparison"][difficulty] = {
                provider: metrics.difficulty_performance.get(difficulty, 0)
                for provider, metrics in self.performance_metrics.items()
            }
        
        # 語言比較
        all_languages = set()
        for metrics in self.performance_metrics.values():
            all_languages.update(metrics.language_performance.keys())
        
        for language in all_languages:
            comparison["language_comparison"][language] = {
                provider: metrics.language_performance.get(language, 0)
                for provider, metrics in self.performance_metrics.items()
            }
        
        return comparison
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """生成使用建議"""
        if not self.performance_metrics:
            return {}
        
        recommendations = {
            "best_overall": "",
            "best_for_accuracy": "",
            "best_for_speed": "",
            "best_for_consistency": "",
            "best_for_edge_cases": "",
            "usage_scenarios": {},
            "improvement_suggestions": []
        }
        
        # 找出各項最佳模型
        best_accuracy = max(self.performance_metrics.items(), key=lambda x: x[1].accuracy)
        best_speed = min(self.performance_metrics.items(), key=lambda x: x[1].avg_response_time)
        best_consistency = max(self.performance_metrics.items(), key=lambda x: x[1].consistency_score)
        best_edge_case = max(self.performance_metrics.items(), key=lambda x: x[1].edge_case_handling)
        
        recommendations["best_for_accuracy"] = f"{best_accuracy[0]} (準確率: {best_accuracy[1].accuracy:.1f}%)"
        recommendations["best_for_speed"] = f"{best_speed[0]} (響應時間: {best_speed[1].avg_response_time:.2f}s)"
        recommendations["best_for_consistency"] = f"{best_consistency[0]} (一致性: {best_consistency[1].consistency_score:.1f}%)"
        recommendations["best_for_edge_cases"] = f"{best_edge_case[0]} (邊界案例: {best_edge_case[1].edge_case_handling:.1f}%)"
        
        # 計算綜合分數
        overall_scores = {}
        for provider, metrics in self.performance_metrics.items():
            # 綜合分數 = 準確率 * 0.4 + 一致性 * 0.3 + (100-錯誤率) * 0.2 + 邊界案例處理 * 0.1
            overall_score = (
                metrics.accuracy * 0.4 +
                metrics.consistency_score * 0.3 +
                (100 - metrics.error_rate) * 0.2 +
                metrics.edge_case_handling * 0.1
            )
            overall_scores[provider] = overall_score
        
        best_overall = max(overall_scores.items(), key=lambda x: x[1])
        recommendations["best_overall"] = f"{best_overall[0]} (綜合分數: {best_overall[1]:.1f})"
        
        # 使用場景建議
        recommendations["usage_scenarios"] = {
            "生產環境": f"推薦 {best_accuracy[0]}，準確率最高",
            "即時應用": f"推薦 {best_speed[0]}，響應速度最快",
            "複雜查詢": f"推薦 {best_edge_case[0]}，邊界案例處理最佳",
            "穩定性要求": f"推薦 {best_consistency[0]}，一致性最高"
        }
        
        # 改進建議
        for provider, metrics in self.performance_metrics.items():
            if metrics.accuracy < 80:
                recommendations["improvement_suggestions"].append(
                    f"{provider}: 準確率偏低({metrics.accuracy:.1f}%)，建議優化提示詞或調整參數"
                )
            if metrics.error_rate > 10:
                recommendations["improvement_suggestions"].append(
                    f"{provider}: 錯誤率較高({metrics.error_rate:.1f}%)，建議檢查API配置和網路連接"
                )
            if metrics.avg_response_time > 5:
                recommendations["improvement_suggestions"].append(
                    f"{provider}: 響應時間較慢({metrics.avg_response_time:.2f}s)，建議優化網路或使用更快的模型"
                )
        
        return recommendations
    
    def _save_results(self, comparison_report: Dict[str, Any]) -> None:
        """保存測試結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存詳細結果
        detailed_filename = f"enhanced_llm_comparison_detailed_{timestamp}.json"
        detailed_data = {
            "comparison_report": comparison_report,
            "raw_results": {
                provider: [asdict(result) for result in results]
                for provider, results in self.results.items()
            },
            "test_cases": [asdict(tc) for tc in self.test_cases]
        }
        
        with open(detailed_filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, ensure_ascii=False, indent=2)
        
        # 保存簡化報告
        summary_filename = f"enhanced_llm_comparison_summary_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 測試結果已保存:")
        print(f"   詳細結果: {detailed_filename}")
        print(f"   摘要報告: {summary_filename}")
    
    def print_summary_report(self) -> None:
        """打印摘要報告"""
        if not self.performance_metrics:
            print("❌ 沒有測試結果可顯示")
            return
        
        print("\n📊 LLM模型比較測試摘要報告")
        print("=" * 60)
        
        # 基本統計
        print(f"\n📋 測試概況:")
        print(f"   測試提供商數量: {len(self.performance_metrics)}")
        print(f"   測試案例總數: {len(self.test_cases)}")
        print(f"   測試類別: {len(set(tc.category for tc in self.test_cases))}個")
        print(f"   難度級別: {len(set(tc.difficulty_level for tc in self.test_cases))}個")
        
        # 性能排名
        print(f"\n🏆 性能排名:")
        
        # 準確率排名
        accuracy_ranking = sorted(self.performance_metrics.items(), 
                                 key=lambda x: x[1].accuracy, reverse=True)
        print(f"\n   📈 準確率排名:")
        for i, (provider, metrics) in enumerate(accuracy_ranking, 1):
            print(f"      {i}. {provider}: {metrics.accuracy:.1f}%")
        
        # 速度排名
        speed_ranking = sorted(self.performance_metrics.items(), 
                              key=lambda x: x[1].avg_response_time)
        print(f"\n   ⚡ 速度排名:")
        for i, (provider, metrics) in enumerate(speed_ranking, 1):
            print(f"      {i}. {provider}: {metrics.avg_response_time:.2f}s")
        
        # 一致性排名
        consistency_ranking = sorted(self.performance_metrics.items(), 
                                    key=lambda x: x[1].consistency_score, reverse=True)
        print(f"\n   🎯 一致性排名:")
        for i, (provider, metrics) in enumerate(consistency_ranking, 1):
            print(f"      {i}. {provider}: {metrics.consistency_score:.1f}%")
        
        # 詳細指標
        print(f"\n📊 詳細指標:")
        for provider, metrics in self.performance_metrics.items():
            print(f"\n   🤖 {provider}:")
            print(f"      準確率: {metrics.accuracy:.1f}%")
            print(f"      平均置信度: {metrics.avg_confidence:.2f}")
            print(f"      平均響應時間: {metrics.avg_response_time:.2f}s")
            print(f"      一致性分數: {metrics.consistency_score:.1f}%")
            print(f"      錯誤率: {metrics.error_rate:.1f}%")
            print(f"      邊界案例處理: {metrics.edge_case_handling:.1f}%")
        
        print("\n" + "=" * 60)


def main():
    """主函數"""
    print("🚀 增強版LLM模型比較測試工具")
    print("=" * 50)
    
    # 創建測試器
    tester = EnhancedLLMModelComparisonTester()
    
    # 獲取可用的提供商
    available_providers = tester.config_manager.get_available_providers()
    
    if not available_providers:
        print("❌ 沒有可用的LLM提供商，請檢查配置")
        return
    
    print(f"📋 發現 {len(available_providers)} 個可用提供商: {[p.value for p in available_providers]}")
    print(f"📊 準備測試 {len(tester.test_cases)} 個測試案例")
    
    # 詢問用戶是否要測試所有提供商
    response = input("\n是否測試所有可用提供商？(y/n): ").lower().strip()
    
    if response == 'y':
        test_providers = available_providers
    else:
        print("\n可用提供商:")
        for i, provider in enumerate(available_providers, 1):
            print(f"  {i}. {provider.value}")
        
        selected_indices = input("\n請輸入要測試的提供商編號（用逗號分隔）: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
            test_providers = [available_providers[i] for i in indices if 0 <= i < len(available_providers)]
        except (ValueError, IndexError):
            print("❌ 輸入格式錯誤，將測試所有提供商")
            test_providers = available_providers
    
    if not test_providers:
        print("❌ 沒有選擇任何提供商")
        return
    
    print(f"\n🎯 將測試以下提供商: {[p.value for p in test_providers]}")
    
    # 運行測試
    try:
        comparison_report = tester.run_model_comparison_test(test_providers)
        
        if comparison_report:
            # 顯示摘要報告
            tester.print_summary_report()
            
            print("\n✅ 測試完成！")
            print("📄 詳細報告已保存到JSON文件中")
        else:
            print("❌ 測試失敗，沒有生成報告")
            
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()