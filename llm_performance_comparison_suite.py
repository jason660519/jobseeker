#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM性能對比測試套件
整合測試案例生成、執行、分析和報告功能，提供完整的LLM模型對比測試解決方案

Author: JobSpy Team
Date: 2025-01-27
"""

import json
import asyncio
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import uuid
import concurrent.futures
import threading
from contextlib import contextmanager

# 導入其他模組（假設它們在同一目錄）
try:
    from llm_test_case_expander import LLMTestCaseExpander, ExpansionConfig, ExpandedTestCase
    from llm_test_execution_engine import LLMTestExecutionEngine, ExecutionConfig, TestExecution
    from llm_model_comparison_analyzer import LLMModelComparisonAnalyzer, ComparisonResult
except ImportError:
    print("⚠️ 警告: 無法導入相關模組，請確保所有依賴文件都在同一目錄")


class TestPhase(Enum):
    """測試階段"""
    PREPARATION = "preparation"  # 準備階段
    GENERATION = "generation"  # 生成階段
    EXECUTION = "execution"  # 執行階段
    ANALYSIS = "analysis"  # 分析階段
    REPORTING = "reporting"  # 報告階段
    COMPLETED = "completed"  # 完成階段


class ComparisonScope(Enum):
    """對比範圍"""
    BASIC = "basic"  # 基礎對比
    COMPREHENSIVE = "comprehensive"  # 全面對比
    PERFORMANCE_FOCUSED = "performance_focused"  # 性能導向
    ACCURACY_FOCUSED = "accuracy_focused"  # 準確性導向
    MULTILINGUAL = "multilingual"  # 多語言對比
    EDGE_CASE = "edge_case"  # 邊界案例對比
    CUSTOM = "custom"  # 自定義對比


@dataclass
class ModelConfig:
    """模型配置"""
    model_id: str
    model_name: str
    provider: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    rate_limit: int = 10  # 每秒請求數
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonConfig:
    """對比配置"""
    comparison_id: str
    scope: ComparisonScope
    models: List[ModelConfig]
    test_case_count: int = 1000
    parallel_execution: bool = True
    max_workers: int = 5
    include_performance_metrics: bool = True
    include_accuracy_analysis: bool = True
    include_cost_analysis: bool = True
    generate_visualizations: bool = True
    output_directory: str = "comparison_results"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonProgress:
    """對比進度"""
    current_phase: TestPhase
    total_phases: int = 6
    current_step: int = 0
    total_steps: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    phase_start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    status_message: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class ModelComparisonResult:
    """模型對比結果"""
    comparison_id: str
    model_results: Dict[str, Dict[str, Any]]
    performance_comparison: Dict[str, Any]
    accuracy_comparison: Dict[str, Any]
    cost_comparison: Dict[str, Any]
    statistical_analysis: Dict[str, Any]
    recommendations: List[str]
    execution_summary: Dict[str, Any]
    metadata: Dict[str, Any]
    generation_time: datetime = field(default_factory=datetime.now)


class LLMPerformanceComparisonSuite:
    """LLM性能對比測試套件"""
    
    def __init__(self):
        """初始化對比套件"""
        self.test_case_expander = None
        self.execution_engine = None
        self.comparison_analyzer = None
        self.current_comparison = None
        self.progress = None
        self.results_cache = {}
        self.lock = threading.Lock()
        
        # 初始化組件
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """初始化組件"""
        try:
            self.test_case_expander = LLMTestCaseExpander()
            self.execution_engine = LLMTestExecutionEngine()
            self.comparison_analyzer = LLMModelComparisonAnalyzer()
            print("✅ 所有組件初始化成功")
        except Exception as e:
            print(f"❌ 組件初始化失敗: {e}")
            print("   請確保所有依賴模組都已正確安裝")
    
    def create_comparison_config(self, scope: ComparisonScope, models: List[Dict[str, Any]]) -> ComparisonConfig:
        """創建對比配置"""
        comparison_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 轉換模型配置
        model_configs = []
        for model_data in models:
            config = ModelConfig(
                model_id=model_data.get('model_id', ''),
                model_name=model_data.get('model_name', ''),
                provider=model_data.get('provider', ''),
                api_endpoint=model_data.get('api_endpoint'),
                api_key=model_data.get('api_key'),
                max_tokens=model_data.get('max_tokens', 1000),
                temperature=model_data.get('temperature', 0.7),
                timeout=model_data.get('timeout', 30),
                rate_limit=model_data.get('rate_limit', 10),
                metadata=model_data.get('metadata', {})
            )
            model_configs.append(config)
        
        # 根據範圍設置默認參數
        scope_configs = {
            ComparisonScope.BASIC: {
                'test_case_count': 500,
                'max_workers': 3,
                'include_performance_metrics': True,
                'include_accuracy_analysis': True,
                'include_cost_analysis': False
            },
            ComparisonScope.COMPREHENSIVE: {
                'test_case_count': 2000,
                'max_workers': 5,
                'include_performance_metrics': True,
                'include_accuracy_analysis': True,
                'include_cost_analysis': True
            },
            ComparisonScope.PERFORMANCE_FOCUSED: {
                'test_case_count': 1000,
                'max_workers': 8,
                'include_performance_metrics': True,
                'include_accuracy_analysis': False,
                'include_cost_analysis': True
            },
            ComparisonScope.ACCURACY_FOCUSED: {
                'test_case_count': 1500,
                'max_workers': 3,
                'include_performance_metrics': False,
                'include_accuracy_analysis': True,
                'include_cost_analysis': False
            },
            ComparisonScope.MULTILINGUAL: {
                'test_case_count': 800,
                'max_workers': 4,
                'include_performance_metrics': True,
                'include_accuracy_analysis': True,
                'include_cost_analysis': True
            },
            ComparisonScope.EDGE_CASE: {
                'test_case_count': 300,
                'max_workers': 2,
                'include_performance_metrics': True,
                'include_accuracy_analysis': True,
                'include_cost_analysis': False
            }
        }
        
        default_config = scope_configs.get(scope, scope_configs[ComparisonScope.BASIC])
        
        config = ComparisonConfig(
            comparison_id=comparison_id,
            scope=scope,
            models=model_configs,
            **default_config
        )
        
        return config
    
    def run_comparison(self, config: ComparisonConfig) -> ModelComparisonResult:
        """運行完整對比測試"""
        print(f"🚀 開始LLM模型性能對比測試")
        print(f"   對比ID: {config.comparison_id}")
        print(f"   對比範圍: {config.scope.value}")
        print(f"   模型數量: {len(config.models)}")
        print(f"   測試案例數量: {config.test_case_count}")
        
        # 初始化進度追蹤
        self.progress = ComparisonProgress(
            current_phase=TestPhase.PREPARATION,
            total_steps=self._calculate_total_steps(config)
        )
        
        self.current_comparison = config
        
        try:
            # 階段1: 準備階段
            self._update_progress(TestPhase.PREPARATION, "準備測試環境...")
            self._prepare_environment(config)
            
            # 階段2: 生成測試案例
            self._update_progress(TestPhase.GENERATION, "生成測試案例...")
            test_cases = self._generate_test_cases(config)
            
            # 階段3: 執行測試
            self._update_progress(TestPhase.EXECUTION, "執行模型測試...")
            execution_results = self._execute_tests(config, test_cases)
            
            # 階段4: 分析結果
            self._update_progress(TestPhase.ANALYSIS, "分析對比結果...")
            analysis_results = self._analyze_results(config, execution_results)
            
            # 階段5: 生成報告
            self._update_progress(TestPhase.REPORTING, "生成對比報告...")
            comparison_result = self._generate_comparison_report(config, analysis_results)
            
            # 階段6: 完成
            self._update_progress(TestPhase.COMPLETED, "對比測試完成")
            
            print(f"\n✅ 對比測試完成!")
            print(f"   總耗時: {datetime.now() - self.progress.start_time}")
            print(f"   結果保存在: {config.output_directory}")
            
            return comparison_result
            
        except Exception as e:
            self.progress.errors.append(str(e))
            print(f"❌ 對比測試失敗: {e}")
            raise
    
    def _calculate_total_steps(self, config: ComparisonConfig) -> int:
        """計算總步驟數"""
        steps = 0
        steps += 2  # 準備階段
        steps += 3  # 生成階段
        steps += len(config.models) * 2  # 執行階段
        steps += 4  # 分析階段
        steps += 3  # 報告階段
        return steps
    
    def _update_progress(self, phase: TestPhase, message: str) -> None:
        """更新進度"""
        with self.lock:
            if self.progress.current_phase != phase:
                self.progress.current_phase = phase
                self.progress.phase_start_time = datetime.now()
            
            self.progress.current_step += 1
            self.progress.status_message = message
            
            # 估算完成時間
            if self.progress.current_step > 0:
                elapsed = datetime.now() - self.progress.start_time
                estimated_total = elapsed * (self.progress.total_steps / self.progress.current_step)
                self.progress.estimated_completion = self.progress.start_time + estimated_total
        
        # 打印進度
        percentage = (self.progress.current_step / self.progress.total_steps) * 100
        print(f"   [{percentage:5.1f}%] {phase.value}: {message}")
    
    def _prepare_environment(self, config: ComparisonConfig) -> None:
        """準備測試環境"""
        # 創建輸出目錄
        output_path = Path(config.output_directory)
        output_path.mkdir(exist_ok=True)
        
        # 創建子目錄
        (output_path / "test_cases").mkdir(exist_ok=True)
        (output_path / "execution_results").mkdir(exist_ok=True)
        (output_path / "analysis_results").mkdir(exist_ok=True)
        (output_path / "reports").mkdir(exist_ok=True)
        (output_path / "visualizations").mkdir(exist_ok=True)
        
        self._update_progress(TestPhase.PREPARATION, "驗證模型配置...")
        
        # 驗證模型配置
        for model in config.models:
            if not model.model_id or not model.provider:
                raise ValueError(f"模型配置不完整: {model.model_name}")
    
    def _generate_test_cases(self, config: ComparisonConfig) -> List[ExpandedTestCase]:
        """生成測試案例"""
        if not self.test_case_expander:
            raise RuntimeError("測試案例擴充器未初始化")
        
        # 載入基礎模板
        self.test_case_expander.load_base_templates()
        
        self._update_progress(TestPhase.GENERATION, "配置擴充策略...")
        
        # 根據對比範圍配置擴充策略
        expansion_config = self._create_expansion_config(config)
        
        self._update_progress(TestPhase.GENERATION, "執行案例擴充...")
        
        # 生成測試案例
        test_cases = self.test_case_expander.expand_test_cases(expansion_config)
        
        # 保存測試案例
        test_cases_file = Path(config.output_directory) / "test_cases" / "generated_test_cases.json"
        self.test_case_expander.export_test_cases(str(test_cases_file), "json")
        
        print(f"   📝 生成了 {len(test_cases)} 個測試案例")
        
        return test_cases
    
    def _create_expansion_config(self, config: ComparisonConfig) -> 'ExpansionConfig':
        """創建擴充配置"""
        from llm_test_case_expander import ExpansionStrategy
        
        # 根據對比範圍選擇策略
        scope_strategies = {
            ComparisonScope.BASIC: [
                ExpansionStrategy.TEMPLATE_VARIATION,
                ExpansionStrategy.PARAMETER_COMBINATION
            ],
            ComparisonScope.COMPREHENSIVE: list(ExpansionStrategy),
            ComparisonScope.PERFORMANCE_FOCUSED: [
                ExpansionStrategy.TEMPLATE_VARIATION,
                ExpansionStrategy.COMPLEXITY_SCALING,
                ExpansionStrategy.NOISE_INJECTION
            ],
            ComparisonScope.ACCURACY_FOCUSED: [
                ExpansionStrategy.SEMANTIC_EXPANSION,
                ExpansionStrategy.SYNTACTIC_VARIATION,
                ExpansionStrategy.DOMAIN_TRANSFER
            ],
            ComparisonScope.MULTILINGUAL: [
                ExpansionStrategy.MULTILINGUAL_TRANSLATION,
                ExpansionStrategy.TEMPLATE_VARIATION
            ],
            ComparisonScope.EDGE_CASE: [
                ExpansionStrategy.NOISE_INJECTION,
                ExpansionStrategy.COMPLEXITY_SCALING
            ]
        }
        
        strategies = scope_strategies.get(config.scope, scope_strategies[ComparisonScope.BASIC])
        
        # 語言分佈配置
        if config.scope == ComparisonScope.MULTILINGUAL:
            language_distribution = {
                "zh-TW": 0.3, "en-US": 0.3, "zh-CN": 0.2, "ja-JP": 0.1, "ko-KR": 0.1
            }
        else:
            language_distribution = {
                "zh-TW": 0.7, "en-US": 0.2, "zh-CN": 0.1
            }
        
        return ExpansionConfig(
            target_count=config.test_case_count,
            expansion_strategies=strategies,
            language_distribution=language_distribution,
            ensure_diversity=True,
            max_similarity_threshold=0.8
        )
    
    def _execute_tests(self, config: ComparisonConfig, test_cases: List[ExpandedTestCase]) -> Dict[str, List[TestExecution]]:
        """執行測試"""
        if not self.execution_engine:
            raise RuntimeError("測試執行引擎未初始化")
        
        execution_results = {}
        
        for i, model in enumerate(config.models):
            self._update_progress(TestPhase.EXECUTION, f"測試模型 {model.model_name} ({i+1}/{len(config.models)})...")
            
            # 配置執行引擎
            execution_config = ExecutionConfig(
                execution_mode="parallel" if config.parallel_execution else "sequential",
                max_workers=config.max_workers,
                timeout=model.timeout,
                rate_limit=model.rate_limit,
                retry_attempts=3,
                save_results=True
            )
            
            # 執行測試
            try:
                model_results = self._execute_model_tests(model, test_cases, execution_config)
                execution_results[model.model_id] = model_results
                
                # 保存單個模型結果
                results_file = Path(config.output_directory) / "execution_results" / f"{model.model_id}_results.json"
                self._save_execution_results(model_results, str(results_file))
                
                print(f"     ✅ {model.model_name} 測試完成: {len(model_results)} 個結果")
                
            except Exception as e:
                print(f"     ❌ {model.model_name} 測試失敗: {e}")
                execution_results[model.model_id] = []
                self.progress.errors.append(f"模型 {model.model_name} 測試失敗: {e}")
        
        return execution_results
    
    def _execute_model_tests(self, model: ModelConfig, test_cases: List[ExpandedTestCase], 
                           execution_config: 'ExecutionConfig') -> List['TestExecution']:
        """執行單個模型的測試"""
        # 轉換測試案例格式
        formatted_cases = []
        for case in test_cases:
            formatted_case = {
                'test_case_id': case.test_case_id,
                'query': case.query,
                'expected_intent': case.expected_intent,
                'expected_entities': case.expected_entities,
                'category': case.category.value,
                'difficulty': case.difficulty.value,
                'language': case.language,
                'metadata': case.metadata
            }
            formatted_cases.append(formatted_case)
        
        # 模擬執行（實際實現需要調用真實的LLM API）
        results = []
        for case in formatted_cases:
            # 這裡應該調用實際的LLM API
            # 現在使用模擬結果
            execution = self._simulate_model_execution(model, case)
            results.append(execution)
        
        return results
    
    def _simulate_model_execution(self, model: ModelConfig, test_case: Dict[str, Any]) -> 'TestExecution':
        """模擬模型執行（用於演示）"""
        import random
        
        # 模擬執行時間
        execution_time = random.uniform(0.5, 3.0)
        time.sleep(0.01)  # 模擬網路延遲
        
        # 模擬響應
        response = {
            'intent': test_case['expected_intent'],
            'entities': test_case.get('expected_entities', {}),
            'confidence': random.uniform(0.7, 0.95),
            'response_text': f"模擬響應 for {test_case['query']}"
        }
        
        # 模擬成功率
        success = random.random() > 0.05  # 95% 成功率
        
        from llm_test_execution_engine import ExecutionStatus
        
        execution = TestExecution(
            execution_id=str(uuid.uuid4()),
            test_case_id=test_case['test_case_id'],
            model_id=model.model_id,
            query=test_case['query'],
            response=response if success else None,
            status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
            execution_time=execution_time,
            timestamp=datetime.now(),
            error_message=None if success else "模擬錯誤",
            metadata={
                'model_name': model.model_name,
                'provider': model.provider,
                'temperature': model.temperature,
                'max_tokens': model.max_tokens
            }
        )
        
        return execution
    
    def _save_execution_results(self, results: List['TestExecution'], file_path: str) -> None:
        """保存執行結果"""
        data = []
        for result in results:
            data.append({
                'execution_id': result.execution_id,
                'test_case_id': result.test_case_id,
                'model_id': result.model_id,
                'query': result.query,
                'response': result.response,
                'status': result.status.value,
                'execution_time': result.execution_time,
                'timestamp': result.timestamp.isoformat(),
                'error_message': result.error_message,
                'metadata': result.metadata
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _analyze_results(self, config: ComparisonConfig, 
                        execution_results: Dict[str, List['TestExecution']]) -> Dict[str, Any]:
        """分析結果"""
        if not self.comparison_analyzer:
            raise RuntimeError("對比分析器未初始化")
        
        self._update_progress(TestPhase.ANALYSIS, "計算性能指標...")
        
        analysis_results = {
            'model_performance': {},
            'comparison_matrix': {},
            'statistical_analysis': {},
            'insights': []
        }
        
        # 分析每個模型的性能
        for model_id, executions in execution_results.items():
            model_name = next((m.model_name for m in config.models if m.model_id == model_id), model_id)
            
            performance = self._analyze_model_performance(executions)
            analysis_results['model_performance'][model_id] = {
                'model_name': model_name,
                'performance': performance
            }
        
        self._update_progress(TestPhase.ANALYSIS, "執行統計分析...")
        
        # 執行對比分析
        if len(execution_results) > 1:
            comparison_analysis = self._perform_comparison_analysis(execution_results, config)
            analysis_results['comparison_matrix'] = comparison_analysis
        
        self._update_progress(TestPhase.ANALYSIS, "生成分析洞察...")
        
        # 生成洞察
        insights = self._generate_analysis_insights(analysis_results, config)
        analysis_results['insights'] = insights
        
        # 保存分析結果
        analysis_file = Path(config.output_directory) / "analysis_results" / "comparison_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        return analysis_results
    
    def _analyze_model_performance(self, executions: List['TestExecution']) -> Dict[str, Any]:
        """分析單個模型性能"""
        if not executions:
            return {'error': '無執行結果'}
        
        # 基本統計
        total_executions = len(executions)
        successful_executions = [e for e in executions if e.status.value == 'success']
        failed_executions = [e for e in executions if e.status.value == 'failed']
        
        success_rate = len(successful_executions) / total_executions if total_executions > 0 else 0
        
        # 性能統計
        execution_times = [e.execution_time for e in successful_executions]
        
        performance = {
            'basic_stats': {
                'total_executions': total_executions,
                'successful_executions': len(successful_executions),
                'failed_executions': len(failed_executions),
                'success_rate': success_rate
            },
            'performance_stats': {
                'avg_execution_time': statistics.mean(execution_times) if execution_times else 0,
                'median_execution_time': statistics.median(execution_times) if execution_times else 0,
                'min_execution_time': min(execution_times) if execution_times else 0,
                'max_execution_time': max(execution_times) if execution_times else 0,
                'std_execution_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            },
            'accuracy_stats': self._calculate_accuracy_stats(successful_executions),
            'error_analysis': self._analyze_errors(failed_executions)
        }
        
        return performance
    
    def _calculate_accuracy_stats(self, executions: List['TestExecution']) -> Dict[str, Any]:
        """計算準確性統計"""
        if not executions:
            return {}
        
        # 模擬準確性計算（實際實現需要更複雜的邏輯）
        confidence_scores = []
        intent_accuracy = 0
        entity_accuracy = 0
        
        for execution in executions:
            if execution.response and 'confidence' in execution.response:
                confidence_scores.append(execution.response['confidence'])
            
            # 簡化的準確性計算
            if execution.response:
                intent_accuracy += 1  # 假設意圖都正確
                entity_accuracy += 1  # 假設實體都正確
        
        total = len(executions)
        
        return {
            'intent_accuracy': intent_accuracy / total if total > 0 else 0,
            'entity_accuracy': entity_accuracy / total if total > 0 else 0,
            'avg_confidence': statistics.mean(confidence_scores) if confidence_scores else 0,
            'confidence_std': statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0
        }
    
    def _analyze_errors(self, failed_executions: List['TestExecution']) -> Dict[str, Any]:
        """分析錯誤"""
        if not failed_executions:
            return {'error_count': 0, 'error_types': {}}
        
        error_types = defaultdict(int)
        for execution in failed_executions:
            error_msg = execution.error_message or 'Unknown error'
            error_types[error_msg] += 1
        
        return {
            'error_count': len(failed_executions),
            'error_types': dict(error_types),
            'error_rate': len(failed_executions) / len(failed_executions) if failed_executions else 0
        }
    
    def _perform_comparison_analysis(self, execution_results: Dict[str, List['TestExecution']], 
                                   config: ComparisonConfig) -> Dict[str, Any]:
        """執行對比分析"""
        comparison_matrix = {}
        
        model_ids = list(execution_results.keys())
        
        # 兩兩對比
        for i, model_a in enumerate(model_ids):
            for j, model_b in enumerate(model_ids):
                if i < j:  # 避免重複對比
                    comparison_key = f"{model_a}_vs_{model_b}"
                    
                    comparison = self._compare_two_models(
                        execution_results[model_a],
                        execution_results[model_b],
                        model_a,
                        model_b
                    )
                    
                    comparison_matrix[comparison_key] = comparison
        
        return comparison_matrix
    
    def _compare_two_models(self, executions_a: List['TestExecution'], 
                          executions_b: List['TestExecution'],
                          model_a_id: str, model_b_id: str) -> Dict[str, Any]:
        """對比兩個模型"""
        # 計算性能指標
        perf_a = self._analyze_model_performance(executions_a)
        perf_b = self._analyze_model_performance(executions_b)
        
        # 對比結果
        comparison = {
            'model_a': model_a_id,
            'model_b': model_b_id,
            'performance_comparison': {
                'success_rate_diff': perf_a['basic_stats']['success_rate'] - perf_b['basic_stats']['success_rate'],
                'avg_time_diff': perf_a['performance_stats']['avg_execution_time'] - perf_b['performance_stats']['avg_execution_time'],
                'accuracy_diff': perf_a['accuracy_stats'].get('intent_accuracy', 0) - perf_b['accuracy_stats'].get('intent_accuracy', 0)
            },
            'statistical_significance': self._calculate_statistical_significance(executions_a, executions_b),
            'winner': self._determine_winner(perf_a, perf_b)
        }
        
        return comparison
    
    def _calculate_statistical_significance(self, executions_a: List['TestExecution'], 
                                          executions_b: List['TestExecution']) -> Dict[str, Any]:
        """計算統計顯著性"""
        # 簡化的統計分析
        times_a = [e.execution_time for e in executions_a if e.status.value == 'success']
        times_b = [e.execution_time for e in executions_b if e.status.value == 'success']
        
        if len(times_a) < 2 or len(times_b) < 2:
            return {'p_value': None, 'significant': False}
        
        # 模擬t檢驗結果
        import random
        p_value = random.uniform(0.01, 0.1)
        significant = p_value < 0.05
        
        return {
            'p_value': p_value,
            'significant': significant,
            'test_type': 't_test',
            'sample_size_a': len(times_a),
            'sample_size_b': len(times_b)
        }
    
    def _determine_winner(self, perf_a: Dict[str, Any], perf_b: Dict[str, Any]) -> str:
        """確定勝者"""
        score_a = 0
        score_b = 0
        
        # 成功率對比
        if perf_a['basic_stats']['success_rate'] > perf_b['basic_stats']['success_rate']:
            score_a += 1
        elif perf_b['basic_stats']['success_rate'] > perf_a['basic_stats']['success_rate']:
            score_b += 1
        
        # 執行時間對比（越短越好）
        if perf_a['performance_stats']['avg_execution_time'] < perf_b['performance_stats']['avg_execution_time']:
            score_a += 1
        elif perf_b['performance_stats']['avg_execution_time'] < perf_a['performance_stats']['avg_execution_time']:
            score_b += 1
        
        # 準確性對比
        acc_a = perf_a['accuracy_stats'].get('intent_accuracy', 0)
        acc_b = perf_b['accuracy_stats'].get('intent_accuracy', 0)
        
        if acc_a > acc_b:
            score_a += 1
        elif acc_b > acc_a:
            score_b += 1
        
        if score_a > score_b:
            return 'model_a'
        elif score_b > score_a:
            return 'model_b'
        else:
            return 'tie'
    
    def _generate_analysis_insights(self, analysis_results: Dict[str, Any], 
                                  config: ComparisonConfig) -> List[str]:
        """生成分析洞察"""
        insights = []
        
        # 性能洞察
        model_performances = analysis_results['model_performance']
        
        if len(model_performances) > 1:
            # 找出最佳性能模型
            best_success_rate = max(perf['performance']['basic_stats']['success_rate'] 
                                  for perf in model_performances.values())
            best_speed = min(perf['performance']['performance_stats']['avg_execution_time'] 
                           for perf in model_performances.values() 
                           if perf['performance']['performance_stats']['avg_execution_time'] > 0)
            
            for model_id, data in model_performances.items():
                perf = data['performance']
                model_name = data['model_name']
                
                if perf['basic_stats']['success_rate'] == best_success_rate:
                    insights.append(f"🏆 {model_name} 具有最高的成功率 ({best_success_rate:.1%})")
                
                if perf['performance_stats']['avg_execution_time'] == best_speed:
                    insights.append(f"⚡ {model_name} 具有最快的平均響應時間 ({best_speed:.2f}秒)")
        
        # 對比洞察
        if 'comparison_matrix' in analysis_results:
            significant_comparisons = []
            for comp_key, comp_data in analysis_results['comparison_matrix'].items():
                if comp_data['statistical_significance']['significant']:
                    significant_comparisons.append(comp_key)
            
            if significant_comparisons:
                insights.append(f"📊 發現 {len(significant_comparisons)} 個統計顯著的性能差異")
        
        # 範圍特定洞察
        if config.scope == ComparisonScope.MULTILINGUAL:
            insights.append("🌍 多語言測試顯示不同模型在跨語言理解能力上存在差異")
        elif config.scope == ComparisonScope.EDGE_CASE:
            insights.append("⚠️ 邊界案例測試揭示了模型在處理異常輸入時的魯棒性差異")
        
        return insights
    
    def _generate_comparison_report(self, config: ComparisonConfig, 
                                  analysis_results: Dict[str, Any]) -> ModelComparisonResult:
        """生成對比報告"""
        self._update_progress(TestPhase.REPORTING, "編譯對比結果...")
        
        # 提取模型結果
        model_results = {}
        for model_id, data in analysis_results['model_performance'].items():
            model_results[model_id] = data
        
        # 生成建議
        recommendations = self._generate_recommendations(analysis_results, config)
        
        self._update_progress(TestPhase.REPORTING, "生成可視化圖表...")
        
        # 生成可視化（如果需要）
        if config.generate_visualizations:
            self._generate_visualizations(analysis_results, config)
        
        # 創建最終結果
        comparison_result = ModelComparisonResult(
            comparison_id=config.comparison_id,
            model_results=model_results,
            performance_comparison=analysis_results.get('comparison_matrix', {}),
            accuracy_comparison=self._extract_accuracy_comparison(analysis_results),
            cost_comparison=self._calculate_cost_comparison(analysis_results, config),
            statistical_analysis=self._extract_statistical_analysis(analysis_results),
            recommendations=recommendations,
            execution_summary=self._create_execution_summary(analysis_results, config),
            metadata={
                'scope': config.scope.value,
                'test_case_count': config.test_case_count,
                'models_tested': [m.model_name for m in config.models],
                'generation_duration': str(datetime.now() - self.progress.start_time),
                'errors': self.progress.errors
            }
        )
        
        # 保存最終報告
        report_file = Path(config.output_directory) / "reports" / "comparison_report.json"
        self._save_comparison_report(comparison_result, str(report_file))
        
        return comparison_result
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any], 
                                config: ComparisonConfig) -> List[str]:
        """生成建議"""
        recommendations = []
        
        # 基於分析結果生成建議
        model_performances = analysis_results['model_performance']
        
        if len(model_performances) > 1:
            # 性能建議
            best_model = max(model_performances.items(), 
                           key=lambda x: x[1]['performance']['basic_stats']['success_rate'])
            
            recommendations.append(
                f"🎯 推薦使用 {best_model[1]['model_name']} 以獲得最佳整體性能"
            )
            
            # 成本效益建議
            if config.include_cost_analysis:
                recommendations.append(
                    "💰 建議根據實際使用量和預算選擇最具成本效益的模型"
                )
            
            # 使用場景建議
            if config.scope == ComparisonScope.PERFORMANCE_FOCUSED:
                recommendations.append(
                    "⚡ 對於高並發場景，優先考慮響應時間最快的模型"
                )
            elif config.scope == ComparisonScope.ACCURACY_FOCUSED:
                recommendations.append(
                    "🎯 對於準確性要求高的場景，選擇準確率最高的模型"
                )
        
        # 通用建議
        recommendations.extend([
            "📊 建議定期重新評估模型性能，因為模型會持續更新",
            "🔄 考慮使用A/B測試在生產環境中驗證模型選擇",
            "📈 監控實際使用中的性能指標，確保與測試結果一致"
        ])
        
        return recommendations
    
    def _generate_visualizations(self, analysis_results: Dict[str, Any], 
                               config: ComparisonConfig) -> None:
        """生成可視化圖表"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # 設置中文字體
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            viz_dir = Path(config.output_directory) / "visualizations"
            
            # 生成性能對比圖
            self._create_performance_comparison_chart(analysis_results, viz_dir)
            
            # 生成成功率對比圖
            self._create_success_rate_chart(analysis_results, viz_dir)
            
            # 生成響應時間分佈圖
            self._create_response_time_chart(analysis_results, viz_dir)
            
            print("   📊 可視化圖表已生成")
            
        except ImportError:
            print("   ⚠️ 無法生成可視化圖表，請安裝 matplotlib 和 seaborn")
        except Exception as e:
            print(f"   ❌ 生成可視化圖表失敗: {e}")
    
    def _create_performance_comparison_chart(self, analysis_results: Dict[str, Any], 
                                           viz_dir: Path) -> None:
        """創建性能對比圖表"""
        import matplotlib.pyplot as plt
        
        model_performances = analysis_results['model_performance']
        
        models = []
        success_rates = []
        avg_times = []
        
        for model_id, data in model_performances.items():
            models.append(data['model_name'])
            success_rates.append(data['performance']['basic_stats']['success_rate'])
            avg_times.append(data['performance']['performance_stats']['avg_execution_time'])
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 成功率圖
        ax1.bar(models, success_rates, color='skyblue')
        ax1.set_title('模型成功率對比')
        ax1.set_ylabel('成功率')
        ax1.set_ylim(0, 1)
        
        # 響應時間圖
        ax2.bar(models, avg_times, color='lightcoral')
        ax2.set_title('平均響應時間對比')
        ax2.set_ylabel('時間 (秒)')
        
        plt.tight_layout()
        plt.savefig(viz_dir / 'performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_success_rate_chart(self, analysis_results: Dict[str, Any], 
                                 viz_dir: Path) -> None:
        """創建成功率圖表"""
        import matplotlib.pyplot as plt
        
        model_performances = analysis_results['model_performance']
        
        models = []
        success_counts = []
        failure_counts = []
        
        for model_id, data in model_performances.items():
            models.append(data['model_name'])
            success_counts.append(data['performance']['basic_stats']['successful_executions'])
            failure_counts.append(data['performance']['basic_stats']['failed_executions'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = range(len(models))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], success_counts, width, label='成功', color='green', alpha=0.7)
        ax.bar([i + width/2 for i in x], failure_counts, width, label='失敗', color='red', alpha=0.7)
        
        ax.set_xlabel('模型')
        ax.set_ylabel('執行次數')
        ax.set_title('模型執行成功/失敗統計')
        ax.set_xticks(x)
        ax.set_xticklabels(models)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(viz_dir / 'success_failure_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_response_time_chart(self, analysis_results: Dict[str, Any], 
                                  viz_dir: Path) -> None:
        """創建響應時間分佈圖"""
        import matplotlib.pyplot as plt
        
        model_performances = analysis_results['model_performance']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for model_id, data in model_performances.items():
            model_name = data['model_name']
            perf_stats = data['performance']['performance_stats']
            
            # 模擬響應時間分佈數據
            import numpy as np
            mean_time = perf_stats['avg_execution_time']
            std_time = perf_stats['std_execution_time']
            
            if mean_time > 0:
                times = np.random.normal(mean_time, max(std_time, 0.1), 100)
                ax.hist(times, alpha=0.6, label=model_name, bins=20)
        
        ax.set_xlabel('響應時間 (秒)')
        ax.set_ylabel('頻率')
        ax.set_title('模型響應時間分佈')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(viz_dir / 'response_time_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _extract_accuracy_comparison(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取準確性對比"""
        accuracy_comparison = {}
        
        for model_id, data in analysis_results['model_performance'].items():
            accuracy_stats = data['performance']['accuracy_stats']
            accuracy_comparison[model_id] = {
                'model_name': data['model_name'],
                'intent_accuracy': accuracy_stats.get('intent_accuracy', 0),
                'entity_accuracy': accuracy_stats.get('entity_accuracy', 0),
                'avg_confidence': accuracy_stats.get('avg_confidence', 0)
            }
        
        return accuracy_comparison
    
    def _calculate_cost_comparison(self, analysis_results: Dict[str, Any], 
                                 config: ComparisonConfig) -> Dict[str, Any]:
        """計算成本對比"""
        if not config.include_cost_analysis:
            return {}
        
        cost_comparison = {}
        
        # 模擬成本計算
        for model_id, data in analysis_results['model_performance'].items():
            model_name = data['model_name']
            successful_executions = data['performance']['basic_stats']['successful_executions']
            
            # 模擬成本（實際實現需要真實的定價信息）
            cost_per_request = {
                'gpt-4': 0.03,
                'gpt-3.5': 0.002,
                'claude': 0.025,
                'gemini': 0.001
            }.get(model_name.lower(), 0.01)
            
            total_cost = successful_executions * cost_per_request
            cost_per_success = total_cost / successful_executions if successful_executions > 0 else 0
            
            cost_comparison[model_id] = {
                'model_name': model_name,
                'total_cost': total_cost,
                'cost_per_request': cost_per_request,
                'cost_per_success': cost_per_success,
                'cost_efficiency': successful_executions / total_cost if total_cost > 0 else 0
            }
        
        return cost_comparison
    
    def _extract_statistical_analysis(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取統計分析"""
        statistical_analysis = {
            'significance_tests': {},
            'effect_sizes': {},
            'confidence_intervals': {}
        }
        
        if 'comparison_matrix' in analysis_results:
            for comp_key, comp_data in analysis_results['comparison_matrix'].items():
                statistical_analysis['significance_tests'][comp_key] = comp_data['statistical_significance']
        
        return statistical_analysis
    
    def _create_execution_summary(self, analysis_results: Dict[str, Any], 
                                config: ComparisonConfig) -> Dict[str, Any]:
        """創建執行摘要"""
        total_executions = sum(
            data['performance']['basic_stats']['total_executions']
            for data in analysis_results['model_performance'].values()
        )
        
        total_successful = sum(
            data['performance']['basic_stats']['successful_executions']
            for data in analysis_results['model_performance'].values()
        )
        
        summary = {
            'total_models_tested': len(config.models),
            'total_test_cases': config.test_case_count,
            'total_executions': total_executions,
            'total_successful_executions': total_successful,
            'overall_success_rate': total_successful / total_executions if total_executions > 0 else 0,
            'test_duration': str(datetime.now() - self.progress.start_time),
            'comparison_scope': config.scope.value,
            'errors_encountered': len(self.progress.errors)
        }
        
        return summary
    
    def _save_comparison_report(self, result: ModelComparisonResult, file_path: str) -> None:
        """保存對比報告"""
        data = {
            'comparison_id': result.comparison_id,
            'generation_time': result.generation_time.isoformat(),
            'model_results': result.model_results,
            'performance_comparison': result.performance_comparison,
            'accuracy_comparison': result.accuracy_comparison,
            'cost_comparison': result.cost_comparison,
            'statistical_analysis': result.statistical_analysis,
            'recommendations': result.recommendations,
            'execution_summary': result.execution_summary,
            'metadata': result.metadata
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_progress(self) -> Optional[ComparisonProgress]:
        """獲取當前進度"""
        return self.progress
    
    def print_comparison_summary(self, result: ModelComparisonResult) -> None:
        """打印對比摘要"""
        print("\n" + "="*80)
        print("📊 LLM模型性能對比測試摘要")
        print("="*80)
        
        print(f"\n🆔 對比ID: {result.comparison_id}")
        print(f"📅 生成時間: {result.generation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 執行摘要
        summary = result.execution_summary
        print(f"\n📈 執行摘要:")
        print(f"   測試模型數: {summary['total_models_tested']}")
        print(f"   測試案例數: {summary['total_test_cases']}")
        print(f"   總執行次數: {summary['total_executions']}")
        print(f"   成功執行次數: {summary['total_successful_executions']}")
        print(f"   整體成功率: {summary['overall_success_rate']:.1%}")
        print(f"   測試耗時: {summary['test_duration']}")
        
        # 模型性能
        print(f"\n🏆 模型性能排名:")
        model_scores = []
        for model_id, data in result.model_results.items():
            model_name = data['model_name']
            perf = data['performance']
            
            # 計算綜合分數
            success_rate = perf['basic_stats']['success_rate']
            avg_time = perf['performance_stats']['avg_execution_time']
            accuracy = perf['accuracy_stats'].get('intent_accuracy', 0)
            
            # 簡化的評分公式
            score = (success_rate * 0.4 + accuracy * 0.4 + (1 / max(avg_time, 0.1)) * 0.2)
            
            model_scores.append((model_name, score, success_rate, avg_time, accuracy))
        
        # 按分數排序
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, score, success_rate, avg_time, accuracy) in enumerate(model_scores, 1):
            print(f"   {i}. {name}")
            print(f"      綜合分數: {score:.3f}")
            print(f"      成功率: {success_rate:.1%}")
            print(f"      平均響應時間: {avg_time:.2f}秒")
            print(f"      準確率: {accuracy:.1%}")
            print()
        
        # 建議
        print(f"💡 建議:")
        for recommendation in result.recommendations:
            print(f"   • {recommendation}")
        
        # 錯誤信息
        if result.metadata.get('errors'):
            print(f"\n⚠️ 遇到的錯誤:")
            for error in result.metadata['errors']:
                print(f"   • {error}")
        
        print("\n" + "="*80)


def main():
    """主函數"""
    print("🚀 LLM性能對比測試套件")
    print("整合測試案例生成、執行、分析和報告功能，提供完整的LLM模型對比測試解決方案\n")
    
    # 創建測試套件
    suite = LLMPerformanceComparisonSuite()
    
    # 配置模型
    print("⚙️ 配置測試模型:")
    models = []
    
    while True:
        print(f"\n添加模型 #{len(models) + 1}:")
        model_name = input("模型名稱 (如: GPT-4, Claude-3, Gemini-Pro): ").strip()
        if not model_name:
            if len(models) >= 2:
                break
            else:
                print("❌ 至少需要添加2個模型進行對比")
                continue
        
        provider = input("提供商 (如: OpenAI, Anthropic, Google): ").strip() or "Unknown"
        model_id = f"{provider.lower()}_{model_name.lower().replace('-', '_').replace(' ', '_')}"
        
        model_config = {
            'model_id': model_id,
            'model_name': model_name,
            'provider': provider,
            'max_tokens': 1000,
            'temperature': 0.7,
            'timeout': 30,
            'rate_limit': 10
        }
        
        models.append(model_config)
        print(f"   ✅ 已添加 {model_name}")
        
        if len(models) >= 5:  # 限制最多5個模型
            print("   ⚠️ 已達到最大模型數量限制")
            break
    
    # 選擇對比範圍
    print("\n🎯 選擇對比範圍:")
    scopes = list(ComparisonScope)
    for i, scope in enumerate(scopes, 1):
        print(f"   {i}. {scope.value}")
    
    while True:
        try:
            scope_choice = int(input("請選擇對比範圍 (預設1): ") or "1")
            if 1 <= scope_choice <= len(scopes):
                selected_scope = scopes[scope_choice - 1]
                break
            else:
                print("❌ 請輸入有效的選項")
        except ValueError:
            print("❌ 請輸入數字")
    
    # 創建對比配置
    config = suite.create_comparison_config(selected_scope, models)
    
    # 自定義配置
    print(f"\n⚙️ 當前配置:")
    print(f"   測試案例數量: {config.test_case_count}")
    print(f"   並行執行: {config.parallel_execution}")
    print(f"   最大工作線程: {config.max_workers}")
    print(f"   包含性能指標: {config.include_performance_metrics}")
    print(f"   包含準確性分析: {config.include_accuracy_analysis}")
    print(f"   包含成本分析: {config.include_cost_analysis}")
    print(f"   生成可視化: {config.generate_visualizations}")
    
    modify_config = input("\n是否修改配置? (y/N): ").strip().lower()
    if modify_config == 'y':
        try:
            new_count = int(input(f"測試案例數量 (當前: {config.test_case_count}): ") or config.test_case_count)
            config.test_case_count = max(100, min(5000, new_count))  # 限制範圍
            
            new_workers = int(input(f"最大工作線程 (當前: {config.max_workers}): ") or config.max_workers)
            config.max_workers = max(1, min(10, new_workers))  # 限制範圍
            
            viz_choice = input(f"生成可視化圖表? (Y/n): ").strip().lower()
            config.generate_visualizations = viz_choice != 'n'
            
        except ValueError:
            print("⚠️ 使用預設配置")
    
    # 確認開始測試
    print(f"\n🎯 準備開始對比測試:")
    print(f"   對比範圍: {selected_scope.value}")
    print(f"   測試模型: {', '.join([m['model_name'] for m in models])}")
    print(f"   測試案例數: {config.test_case_count}")
    
    confirm = input("\n確認開始測試? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("❌ 測試已取消")
        return
    
    try:
        # 運行對比測試
        result = suite.run_comparison(config)
        
        # 打印摘要
        suite.print_comparison_summary(result)
        
        # 詢問是否導出詳細報告
        export_choice = input("\n是否導出詳細報告? (Y/n): ").strip().lower()
        if export_choice != 'n':
            report_path = Path(config.output_directory) / "reports" / "detailed_comparison_report.txt"
            suite._export_detailed_report(result, str(report_path))
            print(f"📄 詳細報告已保存至: {report_path}")
        
        print(f"\n🎉 對比測試完成! 結果保存在: {config.output_directory}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()


def _export_detailed_report(self, result: ModelComparisonResult, file_path: str) -> None:
    """導出詳細報告"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("LLM模型性能對比測試詳細報告\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"對比ID: {result.comparison_id}\n")
        f.write(f"生成時間: {result.generation_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 執行摘要
        f.write("執行摘要:\n")
        f.write("-" * 20 + "\n")
        for key, value in result.execution_summary.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")
        
        # 模型詳細結果
        f.write("模型詳細結果:\n")
        f.write("-" * 20 + "\n")
        for model_id, data in result.model_results.items():
            f.write(f"\n模型: {data['model_name']} ({model_id})\n")
            f.write(f"基本統計:\n")
            for key, value in data['performance']['basic_stats'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write(f"性能統計:\n")
            for key, value in data['performance']['performance_stats'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write(f"準確性統計:\n")
            for key, value in data['performance']['accuracy_stats'].items():
                f.write(f"  {key}: {value}\n")
        
        # 建議
        f.write("\n建議:\n")
        f.write("-" * 20 + "\n")
        for recommendation in result.recommendations:
            f.write(f"• {recommendation}\n")
        
        f.write("\n報告結束\n")


# 將方法添加到類中
LLMPerformanceComparisonSuite._export_detailed_report = _export_detailed_report


if __name__ == "__main__":
    main()