#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM基準測試套件
提供標準化的LLM模型基準測試，包含多維度評估指標

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import asyncio
import statistics
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from enum import Enum
import hashlib
import random
from pathlib import Path

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from jobseeker.llm_config import LLMConfigManager


class BenchmarkCategory(Enum):
    """基準測試類別"""
    ACCURACY = "accuracy"  # 準確性測試
    SPEED = "speed"  # 速度測試
    CONSISTENCY = "consistency"  # 一致性測試
    ROBUSTNESS = "robustness"  # 魯棒性測試
    SCALABILITY = "scalability"  # 擴展性測試
    EDGE_CASES = "edge_cases"  # 邊界案例測試
    MULTILINGUAL = "multilingual"  # 多語言測試
    CONTEXT_UNDERSTANDING = "context_understanding"  # 上下文理解測試
    SEMANTIC_SIMILARITY = "semantic_similarity"  # 語義相似性測試
    ADVERSARIAL = "adversarial"  # 對抗性測試


class TestDifficulty(Enum):
    """測試難度等級"""
    TRIVIAL = "trivial"  # 極簡單
    EASY = "easy"  # 簡單
    MEDIUM = "medium"  # 中等
    HARD = "hard"  # 困難
    EXPERT = "expert"  # 專家級


class LanguageVariant(Enum):
    """語言變體"""
    ZH_TW = "zh_tw"  # 繁體中文
    ZH_CN = "zh_cn"  # 簡體中文
    EN_US = "en_us"  # 美式英語
    EN_GB = "en_gb"  # 英式英語
    JA = "ja"  # 日語
    KO = "ko"  # 韓語
    ES = "es"  # 西班牙語
    FR = "fr"  # 法語
    DE = "de"  # 德語
    MIXED = "mixed"  # 混合語言


@dataclass
class BenchmarkTestCase:
    """基準測試案例"""
    id: str
    category: BenchmarkCategory
    difficulty: TestDifficulty
    language: LanguageVariant
    query: str
    expected_job_related: bool
    expected_intent_type: Optional[str] = None
    expected_entities: Optional[Dict[str, List[str]]] = None
    context: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    weight: float = 1.0  # 測試權重
    timeout: float = 30.0  # 超時時間（秒）
    description: str = ""
    reference_answer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """基準測試結果"""
    test_case_id: str
    provider: str
    success: bool
    accuracy_score: float
    response_time: float
    confidence: float
    predicted_job_related: bool
    predicted_intent_type: Optional[str]
    extracted_entities: Optional[Dict[str, List[str]]]
    error_message: Optional[str]
    reasoning: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkMetrics:
    """基準測試指標"""
    provider: str
    category: BenchmarkCategory
    total_tests: int
    passed_tests: int
    failed_tests: int
    accuracy: float
    weighted_accuracy: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    avg_confidence: float
    confidence_std: float
    error_rate: float
    consistency_score: float
    throughput: float  # 每秒處理的查詢數
    difficulty_breakdown: Dict[str, float]
    language_breakdown: Dict[str, float]


class LLMBenchmarkTestSuite:
    """LLM基準測試套件"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化測試套件"""
        self.config_manager = LLMConfigManager()
        self.test_cases: List[BenchmarkTestCase] = []
        self.results: List[BenchmarkResult] = []
        self.metrics: Dict[str, Dict[BenchmarkCategory, BenchmarkMetrics]] = {}
        self.config_file = config_file
        
        # 載入測試案例
        self._load_benchmark_test_cases()
        
        # 設置隨機種子以確保可重現性
        random.seed(42)
        np.random.seed(42)
    
    def _load_benchmark_test_cases(self) -> None:
        """載入基準測試案例"""
        print("📋 載入基準測試案例...")
        
        # 準確性測試案例
        self._add_accuracy_test_cases()
        
        # 速度測試案例
        self._add_speed_test_cases()
        
        # 一致性測試案例
        self._add_consistency_test_cases()
        
        # 魯棒性測試案例
        self._add_robustness_test_cases()
        
        # 多語言測試案例
        self._add_multilingual_test_cases()
        
        # 邊界案例測試
        self._add_edge_cases_test_cases()
        
        # 上下文理解測試
        self._add_context_understanding_test_cases()
        
        # 語義相似性測試
        self._add_semantic_similarity_test_cases()
        
        # 對抗性測試
        self._add_adversarial_test_cases()
        
        print(f"   ✅ 載入了 {len(self.test_cases)} 個測試案例")
    
    def _add_accuracy_test_cases(self) -> None:
        """添加準確性測試案例"""
        accuracy_cases = [
            # 基礎求職查詢
            BenchmarkTestCase(
                id="acc_001",
                category=BenchmarkCategory.ACCURACY,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.ZH_TW,
                query="我想找軟體工程師的工作",
                expected_job_related=True,
                expected_intent_type="job_search",
                expected_entities={"job_titles": ["軟體工程師"]},
                description="基礎求職意圖識別",
                weight=1.0
            ),
            BenchmarkTestCase(
                id="acc_002",
                category=BenchmarkCategory.ACCURACY,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.EN_US,
                query="Looking for data scientist positions",
                expected_job_related=True,
                expected_intent_type="job_search",
                expected_entities={"job_titles": ["data scientist"]},
                description="英文基礎求職查詢",
                weight=1.0
            ),
            # 複雜求職查詢
            BenchmarkTestCase(
                id="acc_003",
                category=BenchmarkCategory.ACCURACY,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="在台北找年薪100萬以上的資深Python開發工程師職位，要求有5年以上經驗",
                expected_job_related=True,
                expected_intent_type="job_search",
                expected_entities={
                    "job_titles": ["Python開發工程師"],
                    "locations": ["台北"],
                    "skills": ["Python"],
                    "salary_range": ["100萬"]
                },
                description="複雜多條件求職查詢",
                weight=1.5
            ),
            # 非求職查詢
            BenchmarkTestCase(
                id="acc_004",
                category=BenchmarkCategory.ACCURACY,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.ZH_TW,
                query="今天天氣如何？",
                expected_job_related=False,
                expected_intent_type="general_inquiry",
                description="非求職相關查詢",
                weight=1.0
            ),
            # 模糊求職查詢
            BenchmarkTestCase(
                id="acc_005",
                category=BenchmarkCategory.ACCURACY,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="我想換個環境，找個有挑戰性的工作",
                expected_job_related=True,
                expected_intent_type="job_search",
                description="模糊求職意圖",
                weight=2.0
            ),
            # 技能導向查詢
            BenchmarkTestCase(
                id="acc_006",
                category=BenchmarkCategory.ACCURACY,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我會React、Node.js和MongoDB，有什麼適合的職位嗎？",
                expected_job_related=True,
                expected_intent_type="skill_based_search",
                expected_entities={
                    "skills": ["React", "Node.js", "MongoDB"]
                },
                description="技能導向求職查詢",
                weight=1.5
            )
        ]
        
        self.test_cases.extend(accuracy_cases)
    
    def _add_speed_test_cases(self) -> None:
        """添加速度測試案例"""
        speed_cases = [
            BenchmarkTestCase(
                id="speed_001",
                category=BenchmarkCategory.SPEED,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.ZH_TW,
                query="找工作",
                expected_job_related=True,
                timeout=5.0,
                description="極簡查詢速度測試",
                weight=1.0
            ),
            BenchmarkTestCase(
                id="speed_002",
                category=BenchmarkCategory.SPEED,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我想在台北找一份軟體開發的工作，薪水希望在60K以上，公司規模不要太小，最好有彈性工時和遠端工作的機會",
                expected_job_related=True,
                timeout=10.0,
                description="中等長度查詢速度測試",
                weight=1.0
            ),
            BenchmarkTestCase(
                id="speed_003",
                category=BenchmarkCategory.SPEED,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="我是一個有10年經驗的全端工程師，精通JavaScript、Python、Java、C#等多種程式語言，熟悉React、Vue、Angular等前端框架，也有豐富的後端開發經驗，包括Node.js、Django、Spring Boot等，資料庫方面熟悉MySQL、PostgreSQL、MongoDB、Redis，雲端服務有AWS、Azure、GCP的使用經驗，DevOps工具如Docker、Kubernetes、Jenkins也都有接觸，現在想找一份技術主管或架構師的職位，希望能在一家有技術挑戰的公司工作，薪資期望在150K以上，地點希望在台北或新竹，公司文化要開放，有學習成長的機會",
                expected_job_related=True,
                timeout=15.0,
                description="長文本查詢速度測試",
                weight=1.0
            )
        ]
        
        self.test_cases.extend(speed_cases)
    
    def _add_consistency_test_cases(self) -> None:
        """添加一致性測試案例（同一查詢多次執行）"""
        base_queries = [
            "我想找前端工程師的工作",
            "Looking for marketing manager position",
            "今天股市如何？",
            "我想轉職到AI領域"
        ]
        
        for i, query in enumerate(base_queries):
            is_job_related = i < 2 or i == 3  # 前兩個和最後一個是求職相關
            
            # 為每個查詢創建多個一致性測試案例
            for j in range(5):  # 每個查詢測試5次
                self.test_cases.append(BenchmarkTestCase(
                    id=f"cons_{i+1:03d}_{j+1}",
                    category=BenchmarkCategory.CONSISTENCY,
                    difficulty=TestDifficulty.MEDIUM,
                    language=LanguageVariant.ZH_TW if i % 2 == 0 else LanguageVariant.EN_US,
                    query=query,
                    expected_job_related=is_job_related,
                    description=f"一致性測試 - 查詢{i+1} 第{j+1}次",
                    weight=1.0,
                    metadata={"consistency_group": f"group_{i+1}", "attempt": j+1}
                ))
    
    def _add_robustness_test_cases(self) -> None:
        """添加魯棒性測試案例"""
        robustness_cases = [
            # 拼寫錯誤
            BenchmarkTestCase(
                id="rob_001",
                category=BenchmarkCategory.ROBUSTNESS,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我想找軟体工程師的工做",  # 故意拼錯
                expected_job_related=True,
                description="拼寫錯誤魯棒性測試",
                weight=1.5
            ),
            # 特殊字符
            BenchmarkTestCase(
                id="rob_002",
                category=BenchmarkCategory.ROBUSTNESS,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我想找@#$%軟體工程師&*()的工作!!!",
                expected_job_related=True,
                description="特殊字符魯棒性測試",
                weight=1.5
            ),
            # 極長查詢
            BenchmarkTestCase(
                id="rob_003",
                category=BenchmarkCategory.ROBUSTNESS,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="找工作" * 100,  # 重複200次
                expected_job_related=True,
                description="極長查詢魯棒性測試",
                weight=2.0
            ),
            # 空白和特殊空格
            BenchmarkTestCase(
                id="rob_004",
                category=BenchmarkCategory.ROBUSTNESS,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="   我想找    軟體工程師   的工作   ",
                expected_job_related=True,
                description="空白字符魯棒性測試",
                weight=1.0
            ),
            # 數字和符號混合
            BenchmarkTestCase(
                id="rob_005",
                category=BenchmarkCategory.ROBUSTNESS,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我想找123軟體工程師456的工作789",
                expected_job_related=True,
                description="數字符號混合魯棒性測試",
                weight=1.5
            )
        ]
        
        self.test_cases.extend(robustness_cases)
    
    def _add_multilingual_test_cases(self) -> None:
        """添加多語言測試案例"""
        multilingual_cases = [
            # 繁體中文
            BenchmarkTestCase(
                id="ml_001",
                category=BenchmarkCategory.MULTILINGUAL,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.ZH_TW,
                query="我想找資料科學家的工作",
                expected_job_related=True,
                description="繁體中文求職查詢",
                weight=1.0
            ),
            # 簡體中文
            BenchmarkTestCase(
                id="ml_002",
                category=BenchmarkCategory.MULTILINGUAL,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.ZH_CN,
                query="我想找数据科学家的工作",
                expected_job_related=True,
                description="簡體中文求職查詢",
                weight=1.0
            ),
            # 英文
            BenchmarkTestCase(
                id="ml_003",
                category=BenchmarkCategory.MULTILINGUAL,
                difficulty=TestDifficulty.EASY,
                language=LanguageVariant.EN_US,
                query="I want to find a data scientist job",
                expected_job_related=True,
                description="英文求職查詢",
                weight=1.0
            ),
            # 日文
            BenchmarkTestCase(
                id="ml_004",
                category=BenchmarkCategory.MULTILINGUAL,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.JA,
                query="データサイエンティストの仕事を探しています",
                expected_job_related=True,
                description="日文求職查詢",
                weight=1.5
            ),
            # 韓文
            BenchmarkTestCase(
                id="ml_005",
                category=BenchmarkCategory.MULTILINGUAL,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.KO,
                query="데이터 사이언티스트 일자리를 찾고 있습니다",
                expected_job_related=True,
                description="韓文求職查詢",
                weight=1.5
            ),
            # 混合語言
            BenchmarkTestCase(
                id="ml_006",
                category=BenchmarkCategory.MULTILINGUAL,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.MIXED,
                query="我想找software engineer的工作，要求會Python和機械學習",
                expected_job_related=True,
                description="中英混合求職查詢",
                weight=2.0
            )
        ]
        
        self.test_cases.extend(multilingual_cases)
    
    def _add_edge_cases_test_cases(self) -> None:
        """添加邊界案例測試"""
        edge_cases = [
            # 極短查詢
            BenchmarkTestCase(
                id="edge_001",
                category=BenchmarkCategory.EDGE_CASES,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="工作",
                expected_job_related=True,
                description="極短查詢邊界測試",
                weight=2.0
            ),
            # 空查詢
            BenchmarkTestCase(
                id="edge_002",
                category=BenchmarkCategory.EDGE_CASES,
                difficulty=TestDifficulty.EXPERT,
                language=LanguageVariant.ZH_TW,
                query="",
                expected_job_related=False,
                description="空查詢邊界測試",
                weight=3.0
            ),
            # 只有標點符號
            BenchmarkTestCase(
                id="edge_003",
                category=BenchmarkCategory.EDGE_CASES,
                difficulty=TestDifficulty.EXPERT,
                language=LanguageVariant.ZH_TW,
                query="？！。，；：",
                expected_job_related=False,
                description="純標點符號邊界測試",
                weight=3.0
            ),
            # 數字查詢
            BenchmarkTestCase(
                id="edge_004",
                category=BenchmarkCategory.EDGE_CASES,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="123456789",
                expected_job_related=False,
                description="純數字邊界測試",
                weight=2.0
            ),
            # 重複字符
            BenchmarkTestCase(
                id="edge_005",
                category=BenchmarkCategory.EDGE_CASES,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="工工工工工工工工工工作作作作作作作作作作",
                expected_job_related=True,
                description="重複字符邊界測試",
                weight=2.0
            )
        ]
        
        self.test_cases.extend(edge_cases)
    
    def _add_context_understanding_test_cases(self) -> None:
        """添加上下文理解測試案例"""
        context_cases = [
            BenchmarkTestCase(
                id="ctx_001",
                category=BenchmarkCategory.CONTEXT_UNDERSTANDING,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我想換工作",
                context="用戶之前提到對目前的軟體開發工作不滿意",
                expected_job_related=True,
                description="基於上下文的求職意圖理解",
                weight=1.5
            ),
            BenchmarkTestCase(
                id="ctx_002",
                category=BenchmarkCategory.CONTEXT_UNDERSTANDING,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="有什麼推薦的嗎？",
                context="用戶剛才詢問了關於資料科學家職位的要求",
                expected_job_related=True,
                description="隱含求職意圖的上下文理解",
                weight=2.0
            )
        ]
        
        self.test_cases.extend(context_cases)
    
    def _add_semantic_similarity_test_cases(self) -> None:
        """添加語義相似性測試案例"""
        semantic_cases = [
            BenchmarkTestCase(
                id="sem_001",
                category=BenchmarkCategory.SEMANTIC_SIMILARITY,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="我想尋找職業機會",
                expected_job_related=True,
                description="語義相似的求職表達",
                weight=1.5
            ),
            BenchmarkTestCase(
                id="sem_002",
                category=BenchmarkCategory.SEMANTIC_SIMILARITY,
                difficulty=TestDifficulty.MEDIUM,
                language=LanguageVariant.ZH_TW,
                query="希望能找到新的工作機會",
                expected_job_related=True,
                description="另一種求職表達方式",
                weight=1.5
            ),
            BenchmarkTestCase(
                id="sem_003",
                category=BenchmarkCategory.SEMANTIC_SIMILARITY,
                difficulty=TestDifficulty.HARD,
                language=LanguageVariant.ZH_TW,
                query="想要轉換跑道",
                expected_job_related=True,
                description="隱喻性的求職表達",
                weight=2.0
            )
        ]
        
        self.test_cases.extend(semantic_cases)
    
    def _add_adversarial_test_cases(self) -> None:
        """添加對抗性測試案例"""
        adversarial_cases = [
            BenchmarkTestCase(
                id="adv_001",
                category=BenchmarkCategory.ADVERSARIAL,
                difficulty=TestDifficulty.EXPERT,
                language=LanguageVariant.ZH_TW,
                query="我不想找工作，但是想了解軟體工程師的薪資",
                expected_job_related=False,  # 明確說不想找工作
                description="對抗性測試 - 明確否定但包含職位關鍵詞",
                weight=3.0
            ),
            BenchmarkTestCase(
                id="adv_002",
                category=BenchmarkCategory.ADVERSARIAL,
                difficulty=TestDifficulty.EXPERT,
                language=LanguageVariant.ZH_TW,
                query="工作真累，我想休息",
                expected_job_related=False,  # 抱怨工作，不是找工作
                description="對抗性測試 - 負面工作情緒",
                weight=3.0
            ),
            BenchmarkTestCase(
                id="adv_003",
                category=BenchmarkCategory.ADVERSARIAL,
                difficulty=TestDifficulty.EXPERT,
                language=LanguageVariant.ZH_TW,
                query="我朋友想找軟體工程師的工作",
                expected_job_related=False,  # 是朋友要找，不是自己
                description="對抗性測試 - 第三人稱求職",
                weight=3.0
            )
        ]
        
        self.test_cases.extend(adversarial_cases)
    
    def run_benchmark(self, providers: Optional[List[LLMProvider]] = None, 
                     categories: Optional[List[BenchmarkCategory]] = None,
                     max_workers: int = 3) -> Dict[str, Any]:
        """運行基準測試"""
        print("🚀 開始LLM基準測試")
        print("=" * 60)
        
        # 確定要測試的提供商
        if providers is None:
            providers = self.config_manager.get_available_providers()
        
        # 確定要測試的類別
        if categories is None:
            categories = list(BenchmarkCategory)
        
        # 過濾測試案例
        filtered_test_cases = [
            tc for tc in self.test_cases 
            if tc.category in categories
        ]
        
        print(f"📋 測試提供商: {[p.value for p in providers]}")
        print(f"🎯 測試類別: {[c.value for c in categories]}")
        print(f"📝 測試案例數量: {len(filtered_test_cases)}")
        print(f"⚡ 並行工作數: {max_workers}")
        
        # 執行測試
        start_time = time.time()
        
        for provider in providers:
            print(f"\n🔄 測試提供商: {provider.value}")
            provider_results = self._run_provider_tests(
                provider, filtered_test_cases, max_workers
            )
            self.results.extend(provider_results)
        
        total_time = time.time() - start_time
        
        # 計算指標
        self._calculate_benchmark_metrics()
        
        # 生成報告
        report = self._generate_benchmark_report(total_time)
        
        # 保存結果
        self._save_benchmark_results(report)
        
        return report
    
    def _run_provider_tests(self, provider: LLMProvider, 
                           test_cases: List[BenchmarkTestCase],
                           max_workers: int) -> List[BenchmarkResult]:
        """運行特定提供商的測試"""
        try:
            analyzer = LLMIntentAnalyzer(provider=provider)
            results = []
            
            # 使用線程池並行執行測試
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_test = {
                    executor.submit(self._execute_test_case, analyzer, test_case): test_case
                    for test_case in test_cases
                }
                
                completed = 0
                total = len(test_cases)
                
                for future in as_completed(future_to_test):
                    test_case = future_to_test[future]
                    completed += 1
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # 顯示進度
                        if completed % 10 == 0 or completed == total:
                            print(f"   進度: {completed}/{total} ({completed/total*100:.1f}%)")
                            
                    except Exception as e:
                        print(f"   ❌ 測試案例 {test_case.id} 失敗: {str(e)}")
                        # 創建失敗結果
                        results.append(BenchmarkResult(
                            test_case_id=test_case.id,
                            provider=provider.value,
                            success=False,
                            accuracy_score=0.0,
                            response_time=0.0,
                            confidence=0.0,
                            predicted_job_related=False,
                            predicted_intent_type=None,
                            extracted_entities=None,
                            error_message=str(e),
                            reasoning="",
                            timestamp=datetime.now().isoformat()
                        ))
            
            print(f"   ✅ 完成 {len(results)} 個測試")
            return results
            
        except Exception as e:
            print(f"   ❌ 提供商 {provider.value} 測試失敗: {str(e)}")
            return []
    
    def _execute_test_case(self, analyzer: LLMIntentAnalyzer, 
                          test_case: BenchmarkTestCase) -> BenchmarkResult:
        """執行單個測試案例"""
        start_time = time.time()
        
        try:
            # 設置超時
            result = analyzer.analyze_intent(test_case.query)
            response_time = time.time() - start_time
            
            # 檢查是否超時
            if response_time > test_case.timeout:
                raise TimeoutError(f"測試超時 ({response_time:.2f}s > {test_case.timeout}s)")
            
            # 計算準確率分數
            accuracy_score = self._calculate_accuracy_score(test_case, result)
            
            # 提取實體
            extracted_entities = None
            if result.structured_intent and result.is_job_related:
                intent = result.structured_intent
                extracted_entities = {
                    "job_titles": getattr(intent, 'job_titles', []),
                    "skills": getattr(intent, 'skills', []),
                    "locations": getattr(intent, 'locations', []),
                    "salary_range": getattr(intent, 'salary_range', None)
                }
            
            return BenchmarkResult(
                test_case_id=test_case.id,
                provider=analyzer.provider.value,
                success=True,
                accuracy_score=accuracy_score,
                response_time=response_time,
                confidence=result.confidence,
                predicted_job_related=result.is_job_related,
                predicted_intent_type=result.intent_type.value if hasattr(result.intent_type, 'value') else str(result.intent_type),
                extracted_entities=extracted_entities,
                error_message=None,
                reasoning=getattr(result, 'llm_reasoning', ''),
                timestamp=datetime.now().isoformat(),
                metadata={
                    "test_category": test_case.category.value,
                    "test_difficulty": test_case.difficulty.value,
                    "test_language": test_case.language.value,
                    "test_weight": test_case.weight
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return BenchmarkResult(
                test_case_id=test_case.id,
                provider=analyzer.provider.value,
                success=False,
                accuracy_score=0.0,
                response_time=response_time,
                confidence=0.0,
                predicted_job_related=False,
                predicted_intent_type=None,
                extracted_entities=None,
                error_message=str(e),
                reasoning="",
                timestamp=datetime.now().isoformat(),
                metadata={
                    "test_category": test_case.category.value,
                    "test_difficulty": test_case.difficulty.value,
                    "test_language": test_case.language.value,
                    "test_weight": test_case.weight
                }
            )
    
    def _calculate_accuracy_score(self, test_case: BenchmarkTestCase, 
                                 result: Any) -> float:
        """計算準確率分數"""
        score = 0.0
        
        # 基礎求職相關性判斷 (權重: 50%)
        if test_case.expected_job_related == result.is_job_related:
            score += 0.5
        
        # 意圖類型匹配 (權重: 20%)
        if test_case.expected_intent_type:
            predicted_intent = result.intent_type.value if hasattr(result.intent_type, 'value') else str(result.intent_type)
            if test_case.expected_intent_type == predicted_intent:
                score += 0.2
        else:
            score += 0.2  # 如果沒有期望的意圖類型，給予滿分
        
        # 實體提取匹配 (權重: 30%)
        if test_case.expected_entities and result.structured_intent and result.is_job_related:
            entity_score = self._calculate_entity_score(test_case.expected_entities, result.structured_intent)
            score += 0.3 * entity_score
        else:
            score += 0.3  # 如果沒有期望的實體，給予滿分
        
        return min(score, 1.0)  # 確保分數不超過1.0
    
    def _calculate_entity_score(self, expected_entities: Dict[str, List[str]], 
                               structured_intent: Any) -> float:
        """計算實體提取分數"""
        if not expected_entities:
            return 1.0
        
        total_score = 0.0
        entity_count = 0
        
        for entity_type, expected_values in expected_entities.items():
            if not expected_values:
                continue
                
            entity_count += 1
            predicted_values = getattr(structured_intent, entity_type, [])
            
            if isinstance(predicted_values, str):
                predicted_values = [predicted_values]
            elif predicted_values is None:
                predicted_values = []
            
            # 計算交集比例
            if predicted_values:
                intersection = set(expected_values) & set(predicted_values)
                entity_score = len(intersection) / len(expected_values)
                total_score += entity_score
        
        return total_score / entity_count if entity_count > 0 else 1.0
    
    def _calculate_benchmark_metrics(self) -> None:
        """計算基準測試指標"""
        print("\n📊 計算基準測試指標...")
        
        # 按提供商和類別分組
        grouped_results = defaultdict(lambda: defaultdict(list))
        
        for result in self.results:
            category = BenchmarkCategory(result.metadata.get("test_category", "accuracy"))
            grouped_results[result.provider][category].append(result)
        
        # 計算每個提供商每個類別的指標
        for provider, category_results in grouped_results.items():
            if provider not in self.metrics:
                self.metrics[provider] = {}
            
            for category, results in category_results.items():
                metrics = self._calculate_category_metrics(provider, category, results)
                self.metrics[provider][category] = metrics
        
        print(f"   ✅ 計算完成，涵蓋 {len(self.metrics)} 個提供商")
    
    def _calculate_category_metrics(self, provider: str, category: BenchmarkCategory, 
                                   results: List[BenchmarkResult]) -> BenchmarkMetrics:
        """計算特定類別的指標"""
        if not results:
            return BenchmarkMetrics(
                provider=provider,
                category=category,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                accuracy=0.0,
                weighted_accuracy=0.0,
                avg_response_time=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                avg_confidence=0.0,
                confidence_std=0.0,
                error_rate=1.0,
                consistency_score=0.0,
                throughput=0.0,
                difficulty_breakdown={},
                language_breakdown={}
            )
        
        # 基本統計
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        # 成功的結果
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            accuracy = 0.0
            weighted_accuracy = 0.0
            avg_response_time = 0.0
            median_response_time = 0.0
            p95_response_time = 0.0
            avg_confidence = 0.0
            confidence_std = 0.0
            consistency_score = 0.0
            throughput = 0.0
        else:
            # 準確率
            accuracy_scores = [r.accuracy_score for r in successful_results]
            accuracy = statistics.mean(accuracy_scores)
            
            # 加權準確率
            weights = [r.metadata.get("test_weight", 1.0) for r in successful_results]
            weighted_accuracy = sum(a * w for a, w in zip(accuracy_scores, weights)) / sum(weights)
            
            # 響應時間
            response_times = [r.response_time for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = np.percentile(response_times, 95)
            
            # 置信度
            confidences = [r.confidence for r in successful_results]
            avg_confidence = statistics.mean(confidences)
            confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
            
            # 一致性分數（針對一致性測試）
            consistency_score = self._calculate_consistency_score_for_category(successful_results)
            
            # 吞吐量（每秒處理的查詢數）
            total_time = sum(response_times)
            throughput = len(successful_results) / total_time if total_time > 0 else 0.0
        
        # 錯誤率
        error_rate = failed_tests / total_tests
        
        # 難度分解
        difficulty_breakdown = self._calculate_difficulty_breakdown(results)
        
        # 語言分解
        language_breakdown = self._calculate_language_breakdown(results)
        
        return BenchmarkMetrics(
            provider=provider,
            category=category,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            accuracy=accuracy,
            weighted_accuracy=weighted_accuracy,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            avg_confidence=avg_confidence,
            confidence_std=confidence_std,
            error_rate=error_rate,
            consistency_score=consistency_score,
            throughput=throughput,
            difficulty_breakdown=difficulty_breakdown,
            language_breakdown=language_breakdown
        )
    
    def _calculate_consistency_score_for_category(self, results: List[BenchmarkResult]) -> float:
        """計算類別的一致性分數"""
        # 找出一致性測試組
        consistency_groups = defaultdict(list)
        
        for result in results:
            group = result.metadata.get("consistency_group")
            if group:
                consistency_groups[group].append(result)
        
        if not consistency_groups:
            return 1.0  # 沒有一致性測試，假設完全一致
        
        group_scores = []
        
        for group, group_results in consistency_groups.items():
            if len(group_results) < 2:
                continue
            
            # 計算該組的一致性
            predictions = [r.predicted_job_related for r in group_results]
            confidences = [r.confidence for r in group_results]
            
            # 預測一致性
            prediction_consistency = len(set(predictions)) == 1
            
            # 置信度一致性
            confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
            confidence_consistency = max(0.0, 1.0 - confidence_std)
            
            group_score = prediction_consistency * 0.7 + confidence_consistency * 0.3
            group_scores.append(group_score)
        
        return statistics.mean(group_scores) if group_scores else 1.0
    
    def _calculate_difficulty_breakdown(self, results: List[BenchmarkResult]) -> Dict[str, float]:
        """計算難度分解"""
        difficulty_groups = defaultdict(list)
        
        for result in results:
            difficulty = result.metadata.get("test_difficulty", "easy")
            if result.success:
                difficulty_groups[difficulty].append(result.accuracy_score)
        
        breakdown = {}
        for difficulty, scores in difficulty_groups.items():
            breakdown[difficulty] = statistics.mean(scores) if scores else 0.0
        
        return breakdown
    
    def _calculate_language_breakdown(self, results: List[BenchmarkResult]) -> Dict[str, float]:
        """計算語言分解"""
        language_groups = defaultdict(list)
        
        for result in results:
            language = result.metadata.get("test_language", "zh_tw")
            if result.success:
                language_groups[language].append(result.accuracy_score)
        
        breakdown = {}
        for language, scores in language_groups.items():
            breakdown[language] = statistics.mean(scores) if scores else 0.0
        
        return breakdown
    
    def _generate_benchmark_report(self, total_time: float) -> Dict[str, Any]:
        """生成基準測試報告"""
        return {
            "benchmark_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_time": total_time,
                "total_providers": len(set(r.provider for r in self.results)),
                "total_test_cases": len(set(r.test_case_id for r in self.results)),
                "total_executions": len(self.results),
                "overall_success_rate": sum(1 for r in self.results if r.success) / len(self.results) if self.results else 0.0
            },
            "provider_metrics": {
                provider: {
                    category.value: asdict(metrics) for category, metrics in category_metrics.items()
                } for provider, category_metrics in self.metrics.items()
            },
            "category_analysis": self._analyze_categories(),
            "provider_rankings": self._generate_provider_rankings(),
            "recommendations": self._generate_benchmark_recommendations(),
            "detailed_results": [asdict(result) for result in self.results]
        }
    
    def _analyze_categories(self) -> Dict[str, Any]:
        """分析各類別的整體表現"""
        category_analysis = {}
        
        for category in BenchmarkCategory:
            category_results = [r for r in self.results if r.metadata.get("test_category") == category.value]
            
            if not category_results:
                continue
            
            successful_results = [r for r in category_results if r.success]
            
            analysis = {
                "total_tests": len(category_results),
                "success_rate": len(successful_results) / len(category_results),
                "avg_accuracy": statistics.mean([r.accuracy_score for r in successful_results]) if successful_results else 0.0,
                "avg_response_time": statistics.mean([r.response_time for r in successful_results]) if successful_results else 0.0,
                "provider_performance": {}
            }
            
            # 各提供商在該類別的表現
            provider_results = defaultdict(list)
            for result in successful_results:
                provider_results[result.provider].append(result)
            
            for provider, results in provider_results.items():
                analysis["provider_performance"][provider] = {
                    "accuracy": statistics.mean([r.accuracy_score for r in results]),
                    "response_time": statistics.mean([r.response_time for r in results]),
                    "test_count": len(results)
                }
            
            category_analysis[category.value] = analysis
        
        return category_analysis
    
    def _generate_provider_rankings(self) -> Dict[str, Any]:
        """生成提供商排名"""
        if not self.metrics:
            return {}
        
        # 計算綜合分數
        provider_scores = {}
        
        for provider, category_metrics in self.metrics.items():
            total_score = 0.0
            total_weight = 0.0
            
            for category, metrics in category_metrics.items():
                # 類別權重
                category_weight = {
                    BenchmarkCategory.ACCURACY: 0.3,
                    BenchmarkCategory.SPEED: 0.2,
                    BenchmarkCategory.CONSISTENCY: 0.2,
                    BenchmarkCategory.ROBUSTNESS: 0.15,
                    BenchmarkCategory.MULTILINGUAL: 0.1,
                    BenchmarkCategory.EDGE_CASES: 0.05
                }.get(category, 0.1)
                
                # 計算類別分數
                accuracy_score = metrics.weighted_accuracy
                speed_score = min(1.0, 5.0 / max(metrics.avg_response_time, 0.1))  # 5秒為基準
                consistency_score = metrics.consistency_score
                error_penalty = 1.0 - metrics.error_rate
                
                category_score = (accuracy_score * 0.4 + speed_score * 0.3 + 
                                consistency_score * 0.2 + error_penalty * 0.1)
                
                total_score += category_score * category_weight
                total_weight += category_weight
            
            provider_scores[provider] = total_score / total_weight if total_weight > 0 else 0.0
        
        # 排名
        ranked_providers = sorted(provider_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "overall_ranking": [
                {"provider": provider, "score": score, "rank": i+1}
                for i, (provider, score) in enumerate(ranked_providers)
            ],
            "category_leaders": self._find_category_leaders(),
            "detailed_scores": provider_scores
        }
    
    def _find_category_leaders(self) -> Dict[str, str]:
        """找出各類別的領先者"""
        category_leaders = {}
        
        for category in BenchmarkCategory:
            best_provider = None
            best_score = -1.0
            
            for provider, category_metrics in self.metrics.items():
                if category in category_metrics:
                    metrics = category_metrics[category]
                    score = metrics.weighted_accuracy
                    
                    if score > best_score:
                        best_score = score
                        best_provider = provider
            
            if best_provider:
                category_leaders[category.value] = best_provider
        
        return category_leaders
    
    def _generate_benchmark_recommendations(self) -> Dict[str, Any]:
        """生成基準測試建議"""
        if not self.metrics:
            return {}
        
        recommendations = {
            "best_overall": None,
            "best_for_accuracy": None,
            "best_for_speed": None,
            "best_for_consistency": None,
            "usage_recommendations": {},
            "improvement_suggestions": []
        }
        
        # 找出各方面的最佳提供商
        provider_rankings = self._generate_provider_rankings()
        if provider_rankings.get("overall_ranking"):
            recommendations["best_overall"] = provider_rankings["overall_ranking"][0]["provider"]
        
        # 各類別最佳
        category_leaders = provider_rankings.get("category_leaders", {})
        recommendations["best_for_accuracy"] = category_leaders.get("accuracy")
        recommendations["best_for_speed"] = category_leaders.get("speed")
        recommendations["best_for_consistency"] = category_leaders.get("consistency")
        
        # 使用場景建議
        recommendations["usage_recommendations"] = {
            "生產環境": recommendations["best_overall"],
            "即時應用": recommendations["best_for_speed"],
            "高準確率需求": recommendations["best_for_accuracy"],
            "穩定性要求": recommendations["best_for_consistency"]
        }
        
        # 改進建議
        for provider, category_metrics in self.metrics.items():
            for category, metrics in category_metrics.items():
                if metrics.error_rate > 0.1:
                    recommendations["improvement_suggestions"].append(
                        f"{provider}在{category.value}類別的錯誤率較高({metrics.error_rate:.1%})，建議檢查配置"
                    )
                
                if metrics.avg_response_time > 10.0:
                    recommendations["improvement_suggestions"].append(
                        f"{provider}在{category.value}類別的響應時間較慢({metrics.avg_response_time:.1f}秒)，建議優化"
                    )
                
                if metrics.consistency_score < 0.7:
                    recommendations["improvement_suggestions"].append(
                        f"{provider}在{category.value}類別的一致性較低({metrics.consistency_score:.1%})，建議調整參數"
                    )
        
        return recommendations
    
    def _save_benchmark_results(self, report: Dict[str, Any]) -> None:
        """保存基準測試結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存完整報告
        full_report_filename = f"llm_benchmark_full_report_{timestamp}.json"
        with open(full_report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存摘要報告
        summary_report = {
            "benchmark_summary": report["benchmark_summary"],
            "provider_rankings": report["provider_rankings"],
            "category_analysis": report["category_analysis"],
            "recommendations": report["recommendations"]
        }
        
        summary_filename = f"llm_benchmark_summary_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式的結果
        csv_filename = f"llm_benchmark_results_{timestamp}.csv"
        results_df = pd.DataFrame([asdict(result) for result in self.results])
        results_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        print(f"\n💾 基準測試結果已保存:")
        print(f"   完整報告: {full_report_filename}")
        print(f"   摘要報告: {summary_filename}")
        print(f"   CSV結果: {csv_filename}")
    
    def print_benchmark_summary(self) -> None:
        """打印基準測試摘要"""
        if not self.metrics:
            print("❌ 沒有基準測試結果可顯示")
            return
        
        print("\n📊 LLM基準測試摘要")
        print("=" * 60)
        
        # 基本統計
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        
        print(f"\n📋 測試概況:")
        print(f"   總測試次數: {total_tests}")
        print(f"   成功測試: {successful_tests}")
        print(f"   整體成功率: {successful_tests/total_tests*100:.1f}%")
        print(f"   測試提供商: {len(set(r.provider for r in self.results))}")
        print(f"   測試類別: {len(set(r.metadata.get('test_category') for r in self.results))}")
        
        # 提供商排名
        provider_rankings = self._generate_provider_rankings()
        if provider_rankings.get("overall_ranking"):
            print(f"\n🏆 提供商排名:")
            for rank_info in provider_rankings["overall_ranking"][:3]:  # 顯示前3名
                print(f"   {rank_info['rank']}. {rank_info['provider']}: {rank_info['score']:.3f}")
        
        # 類別表現
        print(f"\n📈 各類別表現:")
        for provider, category_metrics in self.metrics.items():
            print(f"\n   {provider}:")
            for category, metrics in category_metrics.items():
                print(f"     {category.value}: 準確率={metrics.weighted_accuracy:.1%}, "
                      f"響應時間={metrics.avg_response_time:.2f}s, "
                      f"錯誤率={metrics.error_rate:.1%}")
        
        # 建議
        recommendations = self._generate_benchmark_recommendations()
        if recommendations.get("best_overall"):
            print(f"\n💡 建議:")
            print(f"   最佳整體表現: {recommendations['best_overall']}")
            print(f"   最佳準確率: {recommendations.get('best_for_accuracy', 'N/A')}")
            print(f"   最佳速度: {recommendations.get('best_for_speed', 'N/A')}")
            print(f"   最佳一致性: {recommendations.get('best_for_consistency', 'N/A')}")


def main():
    """主函數 - 基準測試工具入口點"""
    print("🚀 LLM基準測試套件")
    print("=" * 60)
    
    # 創建測試套件
    benchmark = LLMBenchmarkTestSuite()
    
    # 選擇測試模式
    print("\n請選擇測試模式:")
    print("1. 快速測試 (準確性 + 速度)")
    print("2. 標準測試 (準確性 + 速度 + 一致性 + 魯棒性)")
    print("3. 全面測試 (所有類別)")
    print("4. 自定義測試")
    
    try:
        choice = input("\n請輸入選擇 (1-4): ").strip()
        
        if choice == "1":
            categories = [BenchmarkCategory.ACCURACY, BenchmarkCategory.SPEED]
            providers = None  # 使用所有可用提供商
        elif choice == "2":
            categories = [
                BenchmarkCategory.ACCURACY,
                BenchmarkCategory.SPEED,
                BenchmarkCategory.CONSISTENCY,
                BenchmarkCategory.ROBUSTNESS
            ]
            providers = None
        elif choice == "3":
            categories = None  # 使用所有類別
            providers = None
        elif choice == "4":
            # 自定義選擇
            print("\n可用的測試類別:")
            for i, category in enumerate(BenchmarkCategory, 1):
                print(f"{i}. {category.value}")
            
            category_choices = input("請輸入要測試的類別編號 (用逗號分隔): ").strip()
            try:
                category_indices = [int(x.strip()) - 1 for x in category_choices.split(",")]
                categories = [list(BenchmarkCategory)[i] for i in category_indices]
            except (ValueError, IndexError):
                print("❌ 無效的類別選擇，使用默認設置")
                categories = [BenchmarkCategory.ACCURACY, BenchmarkCategory.SPEED]
            
            providers = None  # 可以進一步擴展提供商選擇
        else:
            print("❌ 無效選擇，使用標準測試")
            categories = [
                BenchmarkCategory.ACCURACY,
                BenchmarkCategory.SPEED,
                BenchmarkCategory.CONSISTENCY,
                BenchmarkCategory.ROBUSTNESS
            ]
            providers = None
        
        # 運行基準測試
        report = benchmark.run_benchmark(providers=providers, categories=categories)
        
        # 顯示摘要
        benchmark.print_benchmark_summary()
        
        print("\n✅ 基準測試完成！")
        print("詳細結果已保存到JSON和CSV文件中。")
        
    except KeyboardInterrupt:
        print("\n❌ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()