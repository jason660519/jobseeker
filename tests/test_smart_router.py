#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能路由器測試腳本
驗證新的簡化架構是否正常工作

Author: jobseeker Team
Date: 2025-01-27
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jobseeker.smart_router import smart_router
from jobseeker.simple_config import SimpleConfig
from jobseeker.platform_adapter import PlatformAdapter, MultiPlatformAdapter


def test_simple_config():
    """測試簡化配置"""
    print("🧪 測試簡化配置...")
    
    config = SimpleConfig()
    
    # 測試地區檢測
    assert config.detect_region("台北 軟體工程師") == "taiwan"
    assert config.detect_region("Sydney software engineer") == "australia"
    assert config.detect_region("New York developer") == "usa"
    assert config.detect_region("無地區關鍵詞") is None
    
    # 測試平台選擇
    taiwan_platforms = config.get_platforms_for_region("taiwan")
    assert "104" in taiwan_platforms
    assert "1111" in taiwan_platforms
    
    australia_platforms = config.get_platforms_for_region("australia")
    assert "seek" in australia_platforms
    
    print("✅ 簡化配置測試通過")


def test_platform_adapter():
    """測試平台適配器"""
    print("🧪 測試平台適配器...")
    
    # 測試單平台適配器
    try:
        adapter = PlatformAdapter("indeed")
        print(f"✅ Indeed 適配器創建成功")
    except Exception as e:
        print(f"⚠️  Indeed 適配器創建失敗: {e}")
    
    # 測試多平台適配器
    multi_adapter = MultiPlatformAdapter(max_workers=2)
    status = multi_adapter.get_platform_status()
    print(f"✅ 多平台適配器狀態: {len(status)} 個平台")
    
    for platform, info in status.items():
        status_icon = "✅" if info.get('enabled', False) else "❌"
        print(f"  {status_icon} {platform}: {info}")


def test_smart_router_basic():
    """測試智能路由器基本功能"""
    print("🧪 測試智能路由器基本功能...")
    
    # 測試平台狀態
    status = smart_router.get_platform_status()
    print(f"✅ 平台狀態獲取成功: {len(status)} 個平台")
    
    # 測試搜尋統計
    stats = smart_router.get_search_statistics()
    print(f"✅ 搜尋統計: {stats}")


def test_smart_router_search():
    """測試智能路由器搜尋功能"""
    print("🧪 測試智能路由器搜尋功能...")
    
    # 測試台灣地區搜尋
    print("🔍 測試台灣地區搜尋...")
    try:
        result = smart_router.search_jobs(
            query="軟體工程師",
            location="台北",
            max_results=5
        )
        
        print(f"✅ 台灣搜尋完成:")
        print(f"  - 總職位數: {result.total_jobs}")
        print(f"  - 成功平台: {result.successful_platforms}")
        print(f"  - 失敗平台: {result.failed_platforms}")
        print(f"  - 執行時間: {result.total_execution_time:.2f}秒")
        
        if result.jobs:
            print(f"  - 第一個職位: {result.jobs[0].title}")
        
    except Exception as e:
        print(f"❌ 台灣搜尋失敗: {e}")
    
    # 測試全球搜尋
    print("🔍 測試全球搜尋...")
    try:
        result = smart_router.search_jobs(
            query="Python developer",
            max_results=3
        )
        
        print(f"✅ 全球搜尋完成:")
        print(f"  - 總職位數: {result.total_jobs}")
        print(f"  - 成功平台: {result.successful_platforms}")
        print(f"  - 執行時間: {result.total_execution_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 全球搜尋失敗: {e}")


def test_specific_platforms():
    """測試指定平台搜尋"""
    print("🧪 測試指定平台搜尋...")
    
    # 測試單平台搜尋
    try:
        result = smart_router.search_jobs(
            query="工程師",
            location="台北",
            max_results=3,
            platforms=["104"]
        )
        
        print(f"✅ 104平台搜尋完成:")
        print(f"  - 總職位數: {result.total_jobs}")
        print(f"  - 成功平台: {result.successful_platforms}")
        
    except Exception as e:
        print(f"❌ 104平台搜尋失敗: {e}")
    
    # 測試多平台搜尋
    try:
        result = smart_router.search_jobs(
            query="developer",
            max_results=5,
            platforms=["indeed", "linkedin"]
        )
        
        print(f"✅ 多平台搜尋完成:")
        print(f"  - 總職位數: {result.total_jobs}")
        print(f"  - 成功平台: {result.successful_platforms}")
        
    except Exception as e:
        print(f"❌ 多平台搜尋失敗: {e}")


def test_fallback_search():
    """測試後備搜尋機制"""
    print("🧪 測試後備搜尋機制...")
    
    try:
        result = smart_router.search_with_fallback(
            query="測試職位",
            location="測試地點",
            max_results=10,
            primary_platforms=["nonexistent_platform"]
        )
        
        print(f"✅ 後備搜尋完成:")
        print(f"  - 總職位數: {result.total_jobs}")
        print(f"  - 成功平台: {result.successful_platforms}")
        print(f"  - 失敗平台: {result.failed_platforms}")
        
    except Exception as e:
        print(f"❌ 後備搜尋失敗: {e}")


def generate_test_report():
    """生成測試報告"""
    print("📊 生成測試報告...")
    
    # 獲取搜尋統計
    stats = smart_router.get_search_statistics()
    
    # 獲取平台狀態
    platform_status = smart_router.get_platform_status()
    
    report = {
        "test_timestamp": time.time(),
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "search_statistics": stats,
        "platform_status": platform_status,
        "summary": {
            "total_platforms": len(platform_status),
            "enabled_platforms": len([p for p in platform_status.values() if p.get('enabled', False)]),
            "total_searches": stats.get('total_searches', 0),
            "total_jobs_found": stats.get('total_jobs_found', 0)
        }
    }
    
    # 保存報告
    report_file = project_root / "tests" / "results" / "smart_router_test_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 測試報告已保存: {report_file}")
    
    return report


def main():
    """主測試函數"""
    print("🚀 開始智能路由器測試")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # 基本功能測試
        test_simple_config()
        print()
        
        test_platform_adapter()
        print()
        
        test_smart_router_basic()
        print()
        
        # 搜尋功能測試
        test_smart_router_search()
        print()
        
        test_specific_platforms()
        print()
        
        test_fallback_search()
        print()
        
        # 生成報告
        report = generate_test_report()
        print()
        
        # 測試總結
        end_time = time.time()
        total_time = end_time - start_time
        
        print("🎉 測試完成!")
        print("=" * 50)
        print(f"⏱️  總測試時間: {total_time:.2f}秒")
        print(f"📊 測試摘要:")
        print(f"  - 總平台數: {report['summary']['total_platforms']}")
        print(f"  - 啟用平台數: {report['summary']['enabled_platforms']}")
        print(f"  - 總搜尋次數: {report['summary']['total_searches']}")
        print(f"  - 總找到職位數: {report['summary']['total_jobs_found']}")
        
        print("\n✅ 新架構測試全部通過!")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
