#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 路由管理器
整合智能路由系統到 jobseeker 主架構

功能:
1. 路由決策執行
2. 代理調度管理
3. 結果聚合
4. 錯誤處理和重試

Author: jobseeker Team
Date: 2025-01-27
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path

# jobseeker 核心導入
try:
    from .intelligent_router import IntelligentRouter, RoutingDecision, AgentType
    from .model import Site
    from . import scrape_jobs as original_scrape_jobs
except ImportError:
    # 開發環境導入
    import sys
    sys.path.append(str(Path(__file__).parent))
    from intelligent_router import IntelligentRouter, RoutingDecision, AgentType
    from model import Site
    import scrape_jobs as original_scrape_jobs

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RouteExecutionResult:
    """路由執行結果"""
    agent: AgentType
    success: bool
    job_count: int
    execution_time: float
    error_message: Optional[str] = None
    jobs_data: Optional[Any] = None

@dataclass
class AggregatedResult:
    """聚合結果"""
    total_jobs: int
    successful_agents: List[AgentType]
    failed_agents: List[AgentType]
    execution_results: List[RouteExecutionResult]
    total_execution_time: float
    routing_decision: RoutingDecision
    combined_jobs_data: Optional[Any] = None

class RouteManager:
    """路由管理器主類"""
    
    # 代理名稱映射
    AGENT_TO_SITE_MAPPING = {
        AgentType.SEEK: "seek",
        AgentType.INDEED: "indeed",
        AgentType.LINKEDIN: "linkedin",
        AgentType.GLASSDOOR: "glassdoor",
        AgentType.ZIPRECRUITER: "zip_recruiter",
        AgentType.NAUKRI: "naukri",
        AgentType.BAYT: "bayt",
        AgentType.BDJOBS: "bdjobs",
        AgentType.GOOGLE: "google",
        AgentType.T104: "104",
        AgentType.JOB1111: "1111",
    }
    # 反向映射：站點字串 -> 代理類型
    SITE_TO_AGENT_MAPPING = {v: k for k, v in AGENT_TO_SITE_MAPPING.items()}
    
    def __init__(self, config_path: Optional[str] = None, max_workers: int = 3):
        """
        初始化路由管理器
        
        Args:
            config_path: 配置文件路徑
            max_workers: 最大並發工作線程數
        """
        self.router = IntelligentRouter(config_path)
        self.max_workers = max_workers
        self.execution_history = []
    
    def smart_scrape_jobs(
        self,
        user_query: str,
        location: Optional[str] = None,
        results_wanted: int = 15,
        hours_old: Optional[int] = None,
        country_indeed: str = 'usa',
        site_name: Optional[str] = None,
        **kwargs
    ) -> AggregatedResult:
        """
        智能爬取工作職位
        
        Args:
            user_query: 用戶查詢（將用於智能路由）
            location: 位置（可選，會與 user_query 結合分析）
            results_wanted: 期望結果數量
            hours_old: 職位發布時間限制
            country_indeed: Indeed 國家設置
            **kwargs: 其他參數
            
        Returns:
            聚合結果
        """
        start_time = time.time()
        
        # 0. 使用者強制單站搜尋（跳過智能路由）
        if site_name:
            start_time = time.time()
            try:
                # 直接呼叫原始爬取函數
                jobs_df = original_scrape_jobs(
                    site_name=[site_name],
                    search_term=user_query,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    country_indeed=country_indeed,
                    **kwargs
                )

                exec_time = time.time() - start_time
                job_count = len(jobs_df) if jobs_df is not None else 0

                agent = self.SITE_TO_AGENT_MAPPING.get(site_name, AgentType.GOOGLE)

                routing_decision = RoutingDecision(
                    selected_agents=[agent],
                    confidence_score=1.0,
                    reasoning=f"User selected single site: {site_name}",
                    geographic_match=None,
                    industry_match=None,
                    fallback_agents=[]
                )

                exec_result = RouteExecutionResult(
                    agent=agent,
                    success=job_count > 0,
                    job_count=job_count,
                    execution_time=exec_time,
                    error_message=None,
                    jobs_data=jobs_df,
                )

                aggregated = AggregatedResult(
                    total_jobs=job_count,
                    successful_agents=[agent] if job_count > 0 else [],
                    failed_agents=[] if job_count > 0 else [agent],
                    execution_results=[exec_result],
                    total_execution_time=exec_time,
                    routing_decision=routing_decision,
                    combined_jobs_data=jobs_df,
                )

                self._log_execution_summary(aggregated)
                return aggregated

            except Exception as e:
                exec_time = time.time() - start_time
                agent = self.SITE_TO_AGENT_MAPPING.get(site_name, AgentType.GOOGLE)
                routing_decision = RoutingDecision(
                    selected_agents=[agent],
                    confidence_score=0.5,
                    reasoning=f"Forced site failed: {site_name}. Error: {e}",
                    geographic_match=None,
                    industry_match=None,
                    fallback_agents=[],
                )
                exec_result = RouteExecutionResult(
                    agent=agent,
                    success=False,
                    job_count=0,
                    execution_time=exec_time,
                    error_message=str(e),
                    jobs_data=None,
                )
                aggregated = AggregatedResult(
                    total_jobs=0,
                    successful_agents=[],
                    failed_agents=[agent],
                    execution_results=[exec_result],
                    total_execution_time=exec_time,
                    routing_decision=routing_decision,
                    combined_jobs_data=None,
                )
                self._log_execution_summary(aggregated)
                return aggregated

        # 1. 智能路由決策
        full_query = f"{user_query} {location or ''}" if location else user_query
        routing_decision = self.router.analyze_query(full_query)
        
        logger.info(f"智能路由決策完成: {[a.value for a in routing_decision.selected_agents]}")
        logger.info(f"決策理由: {routing_decision.reasoning}")
        
        # 2. 執行並發爬取
        execution_results = self._execute_parallel_scraping(
            routing_decision.selected_agents,
            user_query,
            location,
            results_wanted,
            hours_old,
            country_indeed,
            **kwargs
        )
        
        # 3. 處理失敗情況 - 使用後備代理
        successful_results = [r for r in execution_results if r.success]
        if not successful_results and routing_decision.fallback_agents:
            logger.warning("所有主要代理失敗，嘗試後備代理")
            
            fallback_results = self._execute_parallel_scraping(
                routing_decision.fallback_agents,
                user_query,
                location,
                results_wanted,
                hours_old,
                country_indeed,
                **kwargs
            )
            execution_results.extend(fallback_results)
            successful_results = [r for r in execution_results if r.success]
        
        # 4. 聚合結果
        total_execution_time = time.time() - start_time
        aggregated_result = self._aggregate_results(
            execution_results, routing_decision, total_execution_time
        )
        
        # 5. 記錄執行歷史
        self.execution_history.append({
            'timestamp': time.time(),
            'query': user_query,
            'location': location,
            'routing_decision': routing_decision,
            'result': aggregated_result
        })
        
        # 6. 輸出摘要
        self._log_execution_summary(aggregated_result)
        
        return aggregated_result
    
    def _execute_parallel_scraping(
        self,
        agents: List[AgentType],
        search_term: str,
        location: Optional[str],
        results_wanted: int,
        hours_old: Optional[int],
        country_indeed: str,
        **kwargs
    ) -> List[RouteExecutionResult]:
        """
        並發執行多個代理的爬取任務
        
        Args:
            agents: 代理列表
            search_term: 搜索詞
            location: 位置
            results_wanted: 期望結果數量
            hours_old: 時間限制
            country_indeed: Indeed 國家設置
            **kwargs: 其他參數
            
        Returns:
            執行結果列表
        """
        results = []
        
        # 過濾出支持的代理
        supported_agents = [
            agent for agent in agents 
            if agent in self.AGENT_TO_SITE_MAPPING
        ]
        
        if not supported_agents:
            logger.warning("沒有支持的代理可用")
            return results
        
        # 計算每個代理的結果數量
        results_per_agent = max(1, results_wanted // len(supported_agents))
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任務
            future_to_agent = {}
            for agent in supported_agents:
                future = executor.submit(
                    self._execute_single_agent,
                    agent,
                    search_term,
                    location,
                    results_per_agent,
                    hours_old,
                    country_indeed,
                    **kwargs
                )
                future_to_agent[future] = agent
            
            # 收集結果
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result(timeout=60)  # 60秒超時
                    results.append(result)
                    logger.info(f"代理 {agent.value} 完成: {result.job_count} 個職位")
                except Exception as e:
                    error_result = RouteExecutionResult(
                        agent=agent,
                        success=False,
                        job_count=0,
                        execution_time=0,
                        error_message=str(e)
                    )
                    results.append(error_result)
                    logger.error(f"代理 {agent.value} 失敗: {e}")
        
        return results
    
    def _execute_single_agent(
        self,
        agent: AgentType,
        search_term: str,
        location: Optional[str],
        results_wanted: int,
        hours_old: Optional[int],
        country_indeed: str,
        **kwargs
    ) -> RouteExecutionResult:
        """
        執行單個代理的爬取任務
        
        Args:
            agent: 代理類型
            search_term: 搜索詞
            location: 位置
            results_wanted: 期望結果數量
            hours_old: 時間限制
            country_indeed: Indeed 國家設置
            **kwargs: 其他參數
            
        Returns:
            執行結果
        """
        start_time = time.time()
        
        try:
            # 獲取對應的站點名稱
            site_name = self.AGENT_TO_SITE_MAPPING[agent]
            
            # 準備參數
            scrape_params = {
                'site_name': [site_name],
                'search_term': search_term,
                'location': location,
                'results_wanted': results_wanted,
                'hours_old': hours_old,
                'country_indeed': country_indeed,
                **kwargs
            }
            
            # 移除 None 值
            scrape_params = {k: v for k, v in scrape_params.items() if v is not None}
            
            logger.info(f"開始執行代理 {agent.value}: {scrape_params}")
            
            # 執行爬取
            jobs_df = original_scrape_jobs(**scrape_params)
            
            execution_time = time.time() - start_time
            job_count = len(jobs_df) if jobs_df is not None else 0
            
            return RouteExecutionResult(
                agent=agent,
                success=True,
                job_count=job_count,
                execution_time=execution_time,
                jobs_data=jobs_df
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # 特殊處理 Glassdoor 地區限制錯誤
            if agent == AgentType.GLASSDOOR and "not available for" in error_msg:
                logger.warning(f"代理 {agent.value} 地區限制: {error_msg}")
                # 對於地區限制錯誤，不記錄為嚴重錯誤
                return RouteExecutionResult(
                    agent=agent,
                    success=False,
                    job_count=0,
                    execution_time=execution_time,
                    error_message=f"地區限制: {error_msg}"
                )
            else:
                logger.error(f"代理 {agent.value} 執行失敗: {e}")
                
            return RouteExecutionResult(
                agent=agent,
                success=False,
                job_count=0,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def _aggregate_results(
        self,
        execution_results: List[RouteExecutionResult],
        routing_decision: RoutingDecision,
        total_execution_time: float
    ) -> AggregatedResult:
        """
        聚合執行結果
        
        Args:
            execution_results: 執行結果列表
            routing_decision: 路由決策
            total_execution_time: 總執行時間
            
        Returns:
            聚合結果
        """
        successful_agents = [r.agent for r in execution_results if r.success]
        failed_agents = [r.agent for r in execution_results if not r.success]
        total_jobs = sum(r.job_count for r in execution_results if r.success)
        
        # 合併工作數據
        combined_jobs_data = None
        successful_results = [r for r in execution_results if r.success and r.jobs_data is not None]
        
        if successful_results:
            try:
                import pandas as pd
                
                # 合併所有成功的結果
                all_jobs = []
                for result in successful_results:
                    if result.jobs_data is not None and not result.jobs_data.empty:
                        # 添加來源標記
                        jobs_copy = result.jobs_data.copy()
                        jobs_copy['source_agent'] = result.agent.value
                        all_jobs.append(jobs_copy)
                
                if all_jobs:
                    combined_jobs_data = pd.concat(all_jobs, ignore_index=True)
                    
                    # 去重（基於職位標題和公司）
                    if 'title' in combined_jobs_data.columns and 'company' in combined_jobs_data.columns:
                        combined_jobs_data = combined_jobs_data.drop_duplicates(
                            subset=['title', 'company'], keep='first'
                        )
                        
                    logger.info(f"合併後總計 {len(combined_jobs_data)} 個唯一職位")
                    
            except Exception as e:
                logger.error(f"合併結果時出錯: {e}")
        
        return AggregatedResult(
            total_jobs=total_jobs,
            successful_agents=successful_agents,
            failed_agents=failed_agents,
            execution_results=execution_results,
            total_execution_time=total_execution_time,
            routing_decision=routing_decision,
            combined_jobs_data=combined_jobs_data
        )
    
    def _log_execution_summary(self, result: AggregatedResult):
        """
        記錄執行摘要
        
        Args:
            result: 聚合結果
        """
        logger.info("=" * 60)
        logger.info("智能路由執行摘要")
        logger.info("=" * 60)
        logger.info(f"總執行時間: {result.total_execution_time:.2f} 秒")
        logger.info(f"總職位數量: {result.total_jobs}")
        logger.info(f"成功代理: {[a.value for a in result.successful_agents]}")
        
        if result.failed_agents:
            logger.info(f"失敗代理: {[a.value for a in result.failed_agents]}")
        
        logger.info(f"路由信心度: {result.routing_decision.confidence_score:.2f}")
        logger.info(f"路由理由: {result.routing_decision.reasoning}")
        
        # 詳細結果
        for exec_result in result.execution_results:
            status = "✓" if exec_result.success else "✗"
            logger.info(
                f"  {status} {exec_result.agent.value}: "
                f"{exec_result.job_count} 職位, "
                f"{exec_result.execution_time:.2f}s"
            )
            if exec_result.error_message:
                logger.info(f"    錯誤: {exec_result.error_message}")
        
        logger.info("=" * 60)
    
    def get_execution_history(self) -> List[Dict]:
        """
        獲取執行歷史
        
        Returns:
            執行歷史列表
        """
        return self.execution_history
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        獲取路由統計信息
        
        Returns:
            統計信息字典
        """
        if not self.execution_history:
            return {"message": "沒有執行歷史"}
        
        # 統計代理使用情況
        agent_usage = {}
        agent_success_rate = {}
        total_executions = len(self.execution_history)
        
        for history in self.execution_history:
            result = history['result']
            
            for exec_result in result.execution_results:
                agent_name = exec_result.agent.value
                
                if agent_name not in agent_usage:
                    agent_usage[agent_name] = {'total': 0, 'success': 0}
                
                agent_usage[agent_name]['total'] += 1
                if exec_result.success:
                    agent_usage[agent_name]['success'] += 1
        
        # 計算成功率
        for agent_name, stats in agent_usage.items():
            agent_success_rate[agent_name] = stats['success'] / stats['total']
        
        return {
            'total_executions': total_executions,
            'agent_usage': agent_usage,
            'agent_success_rate': agent_success_rate,
            'average_execution_time': sum(
                h['result'].total_execution_time for h in self.execution_history
            ) / total_executions
        }


# 便利函數
def smart_scrape_jobs(
    user_query: str,
    location: Optional[str] = None,
    results_wanted: int = 15,
    hours_old: Optional[int] = None,
    country_indeed: str = 'usa',
    site_name: Optional[str] = None,
    **kwargs
) -> AggregatedResult:
    """
    智能爬取工作職位的便利函數
    
    Args:
        user_query: 用戶查詢（將用於智能路由）
        location: 位置（可選）
        results_wanted: 期望結果數量
        hours_old: 職位發布時間限制
        country_indeed: Indeed 國家設置
        **kwargs: 其他參數
        
    Returns:
        聚合結果
    """
    manager = RouteManager()
    return manager.smart_scrape_jobs(
        user_query=user_query,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed=country_indeed,
        site_name=site_name,
        **kwargs
    )


def demo_route_manager():
    """
    演示路由管理器
    """
    manager = RouteManager()
    
    # 測試查詢
    test_query = "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作"
    
    print("=" * 60)
    print("jobseeker 路由管理器演示")
    print("=" * 60)
    print(f"測試查詢: {test_query}")
    print()
    
    try:
        # 執行智能爬取
        result = manager.smart_scrape_jobs(
            user_query=test_query,
            results_wanted=10
        )
        
        print("\n執行完成！")
        print(f"找到 {result.total_jobs} 個職位")
        
        if result.combined_jobs_data is not None:
            print("\n前5個職位:")
            print(result.combined_jobs_data.head())
        
        # 顯示統計信息
        stats = manager.get_routing_statistics()
        print("\n統計信息:")
        print(stats)
        
    except Exception as e:
        print(f"演示執行失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_route_manager()
