#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台智能路由系統使用示例
演示如何使用整合的多平台API進行職位搜尋

Author: JobSpy Team
Date: 2025-01-27
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# 導入多平台組件
from multi_platform_scheduler import (
    MultiPlatformScheduler, PlatformType, RegionType, TaskStatus
)
from platform_sync_manager import (
    PlatformSyncManager, SyncEventType
)
from data_integrity_manager import (
    DataIntegrityManager, ValidationLevel
)
from multi_platform_config import (
    get_config, ConfigLevel, get_platforms_for_region
)
from integrated_multi_platform_api import IntegratedMultiPlatformAPI


class MultiPlatformDemo:
    """多平台系統演示類"""
    
    def __init__(self):
        """初始化演示"""
        self.config = get_config()
        self.api = IntegratedMultiPlatformAPI(
            redis_url=self.config.get_redis_url(),
            max_concurrent_jobs=self.config.scheduler.max_concurrent_jobs
        )
        
        # 測試案例
        self.test_cases = [
            {
                "name": "美國軟體工程師搜尋",
                "query": "software engineer",
                "location": "San Francisco, CA",
                "region": "us",
                "expected_platforms": ["linkedin", "indeed", "google"]
            },
            {
                "name": "台灣資料科學家搜尋",
                "query": "data scientist",
                "location": "台北市",
                "region": "taiwan",
                "expected_platforms": ["job_bank_1111", "job_bank_104"]
            },
            {
                "name": "澳洲產品經理搜尋",
                "query": "product manager",
                "location": "Sydney, Australia",
                "region": "australia",
                "expected_platforms": ["seek", "linkedin"]
            },
            {
                "name": "全球遠程工作搜尋",
                "query": "remote developer",
                "location": "remote",
                "region": "global",
                "expected_platforms": ["linkedin", "indeed", "google"]
            }
        ]
    
    async def run_demo(self):
        """運行完整演示"""
        print("=" * 80)
        print("多平台智能路由系統演示")
        print("=" * 80)
        
        try:
            # 初始化系統
            await self._initialize_system()
            
            # 顯示系統配置
            await self._show_system_config()
            
            # 運行測試案例
            await self._run_test_cases()
            
            # 顯示系統狀態
            await self._show_system_status()
            
            # 演示併發搜尋
            await self._demo_concurrent_search()
            
            # 演示錯誤處理
            await self._demo_error_handling()
            
        except Exception as e:
            print(f"演示過程中發生錯誤: {e}")
        
        finally:
            # 清理資源
            await self._cleanup()
    
    async def _initialize_system(self):
        """初始化系統"""
        print("\n🚀 正在初始化多平台智能路由系統...")
        
        # 初始化API
        await self.api.initialize()
        await self.api.start()
        
        print("✅ 系統初始化完成")
    
    async def _show_system_config(self):
        """顯示系統配置"""
        print("\n📋 系統配置信息:")
        print("-" * 50)
        
        # 顯示配置級別
        print(f"配置級別: {self.config.config_level.value}")
        
        # 顯示啟用的平台
        enabled_platforms = self.config.get_enabled_platforms()
        print(f"啟用平台: {', '.join(enabled_platforms)}")
        
        # 顯示地區配置
        print("\n地區平台映射:")
        for region_name, region_config in self.config.regions.items():
            platforms = self.config.get_platforms_for_region(region_name)
            print(f"  {region_config.display_name} ({region_name}): {', '.join(platforms)}")
        
        # 顯示調度器配置
        print(f"\n調度器配置:")
        print(f"  最大併發任務: {self.config.scheduler.max_concurrent_jobs}")
        print(f"  最大隊列大小: {self.config.scheduler.max_queue_size}")
        print(f"  任務超時時間: {self.config.scheduler.job_timeout_minutes} 分鐘")
    
    async def _run_test_cases(self):
        """運行測試案例"""
        print("\n🧪 運行測試案例:")
        print("=" * 50)
        
        job_ids = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n測試案例 {i}: {test_case['name']}")
            print("-" * 30)
            
            try:
                # 提交搜尋任務
                job_id = await self.api.scheduler.submit_search_job(
                    query=test_case['query'],
                    location=test_case['location'],
                    region=RegionType(test_case['region']),
                    priority=1,
                    user_id=f"demo_user_{i}"
                )
                
                job_ids.append(job_id)
                
                print(f"✅ 任務已提交: {job_id}")
                print(f"   查詢: {test_case['query']}")
                print(f"   地點: {test_case['location']}")
                print(f"   地區: {test_case['region']}")
                print(f"   預期平台: {', '.join(test_case['expected_platforms'])}")
                
                # 等待一小段時間讓任務開始處理
                await asyncio.sleep(1)
                
                # 檢查任務狀態
                job_status = self.api.scheduler.get_job_status(job_id)
                if job_status:
                    print(f"   當前狀態: {job_status['overall_status']}")
                    print(f"   目標平台: {', '.join(job_status['target_platforms'])}")
                    
                    # 驗證平台選擇是否正確
                    actual_platforms = set(job_status['target_platforms'])
                    expected_platforms = set(test_case['expected_platforms'])
                    
                    if actual_platforms == expected_platforms:
                        print("   ✅ 平台選擇正確")
                    else:
                        print(f"   ⚠️  平台選擇差異: 實際={actual_platforms}, 預期={expected_platforms}")
                
            except Exception as e:
                print(f"   ❌ 測試案例失敗: {e}")
        
        # 等待任務處理
        print("\n⏳ 等待任務處理...")
        await self._wait_for_jobs(job_ids, timeout=60)
    
    async def _wait_for_jobs(self, job_ids: List[str], timeout: int = 60):
        """等待任務完成"""
        start_time = time.time()
        completed_jobs = set()
        
        while len(completed_jobs) < len(job_ids) and (time.time() - start_time) < timeout:
            for job_id in job_ids:
                if job_id in completed_jobs:
                    continue
                
                job_status = self.api.scheduler.get_job_status(job_id)
                if job_status and job_status['overall_status'] in ['completed', 'failed']:
                    completed_jobs.add(job_id)
                    print(f"   📋 任務 {job_id[:8]}... 已完成: {job_status['overall_status']}")
            
            await asyncio.sleep(2)
        
        if len(completed_jobs) < len(job_ids):
            print(f"   ⚠️  超時: {len(job_ids) - len(completed_jobs)} 個任務未完成")
        else:
            print(f"   ✅ 所有 {len(job_ids)} 個任務已完成")
    
    async def _show_system_status(self):
        """顯示系統狀態"""
        print("\n📊 系統狀態:")
        print("-" * 30)
        
        try:
            # 獲取調度器狀態
            scheduler_status = self.api.scheduler.get_scheduler_status()
            print(f"調度器運行狀態: {'✅ 運行中' if scheduler_status['running'] else '❌ 已停止'}")
            print(f"待處理任務: {scheduler_status['pending_jobs']}")
            print(f"活躍任務: {scheduler_status['active_jobs_summary']['total_active_jobs']}")
            print(f"已完成任務: {scheduler_status['active_jobs_summary']['total_completed_jobs']}")
            
            # 獲取同步管理器狀態
            sync_status = self.api.sync_manager.get_sync_status()
            print(f"\n同步管理器運行狀態: {'✅ 運行中' if sync_status['running'] else '❌ 已停止'}")
            
            # 顯示平台健康狀態
            print("\n平台健康狀態:")
            for platform, health in sync_status['platform_health'].items():
                status_icon = "✅" if health['is_healthy'] else "❌"
                print(f"  {status_icon} {platform}: 成功率 {health['success_rate']:.1%}, 響應時間 {health['average_response_time']:.1f}s")
            
            # 獲取完整性摘要
            integrity_summary = self.api.integrity_manager.get_global_integrity_summary()
            print(f"\n數據完整性:")
            print(f"  總檢查次數: {integrity_summary['total_checks']}")
            print(f"  通過檢查: {integrity_summary['passed_checks']}")
            print(f"  平均質量分數: {integrity_summary['average_quality_score']:.2f}")
            
        except Exception as e:
            print(f"獲取系統狀態失敗: {e}")
    
    async def _demo_concurrent_search(self):
        """演示併發搜尋"""
        print("\n🔄 演示併發搜尋:")
        print("-" * 30)
        
        # 創建多個併發搜尋任務
        concurrent_searches = [
            {"query": "python developer", "location": "New York", "region": "us"},
            {"query": "前端工程師", "location": "台北", "region": "taiwan"},
            {"query": "data analyst", "location": "Sydney", "region": "australia"},
            {"query": "machine learning engineer", "location": "remote", "region": "global"},
            {"query": "devops engineer", "location": "California", "region": "us"}
        ]
        
        print(f"同時提交 {len(concurrent_searches)} 個搜尋任務...")
        
        # 同時提交所有任務
        start_time = time.time()
        job_ids = []
        
        for search in concurrent_searches:
            try:
                job_id = await self.api.scheduler.submit_search_job(
                    query=search['query'],
                    location=search['location'],
                    region=RegionType(search['region']),
                    priority=2,
                    user_id="concurrent_demo"
                )
                job_ids.append(job_id)
                print(f"  ✅ 已提交: {search['query']} @ {search['location']}")
            except Exception as e:
                print(f"  ❌ 提交失敗: {search['query']} - {e}")
        
        submission_time = time.time() - start_time
        print(f"\n任務提交耗時: {submission_time:.2f} 秒")
        
        # 監控併發執行
        print("\n監控併發執行進度...")
        await self._monitor_concurrent_execution(job_ids)
    
    async def _monitor_concurrent_execution(self, job_ids: List[str]):
        """監控併發執行"""
        start_time = time.time()
        completed_jobs = set()
        
        while len(completed_jobs) < len(job_ids) and (time.time() - start_time) < 120:
            # 顯示進度
            active_count = 0
            pending_count = 0
            
            for job_id in job_ids:
                if job_id in completed_jobs:
                    continue
                
                job_status = self.api.scheduler.get_job_status(job_id)
                if job_status:
                    status = job_status['overall_status']
                    if status in ['completed', 'failed']:
                        completed_jobs.add(job_id)
                    elif status == 'processing':
                        active_count += 1
                    else:
                        pending_count += 1
            
            progress = len(completed_jobs) / len(job_ids) * 100
            print(f"\r  進度: {progress:.1f}% | 已完成: {len(completed_jobs)} | 處理中: {active_count} | 等待中: {pending_count}", end="")
            
            await asyncio.sleep(3)
        
        print(f"\n\n併發執行完成，總耗時: {time.time() - start_time:.2f} 秒")
    
    async def _demo_error_handling(self):
        """演示錯誤處理"""
        print("\n🚨 演示錯誤處理:")
        print("-" * 30)
        
        # 測試無效地區
        try:
            print("測試無效地區...")
            job_id = await self.api.scheduler.submit_search_job(
                query="test job",
                location="unknown location",
                region=None,  # 這會觸發自動檢測
                priority=1
            )
            print(f"  ✅ 任務已提交（自動檢測地區）: {job_id}")
        except Exception as e:
            print(f"  ❌ 預期錯誤: {e}")
        
        # 測試空查詢
        try:
            print("\n測試空查詢...")
            job_id = await self.api.scheduler.submit_search_job(
                query="",
                location="test location",
                region=RegionType.US,
                priority=1
            )
            print(f"  ⚠️  意外成功: {job_id}")
        except Exception as e:
            print(f"  ✅ 正確拒絕空查詢: {e}")
        
        # 測試系統負載
        print("\n測試系統負載限制...")
        overload_jobs = []
        max_jobs = self.config.scheduler.max_concurrent_jobs + 5
        
        for i in range(max_jobs):
            try:
                job_id = await self.api.scheduler.submit_search_job(
                    query=f"overload test {i}",
                    location="test location",
                    region=RegionType.GLOBAL,
                    priority=3
                )
                overload_jobs.append(job_id)
            except Exception as e:
                print(f"  ⚠️  任務 {i} 被拒絕: {e}")
                break
        
        print(f"  成功提交 {len(overload_jobs)} 個負載測試任務")
    
    async def _cleanup(self):
        """清理資源"""
        print("\n🧹 清理系統資源...")
        
        try:
            await self.api.stop()
            print("✅ 系統已停止")
        except Exception as e:
            print(f"❌ 清理過程中發生錯誤: {e}")


async def main():
    """主函數"""
    demo = MultiPlatformDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # 運行演示
    print("啟動多平台智能路由系統演示...")
    asyncio.run(main())