#!/usr/bin/env python3
"""
增強版爬蟲最終測試腳本
測試 ZipRecruiter、Google Jobs 和 Bayt 的修復效果
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_scrapers_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_imports():
    """測試所有增強版爬蟲模組的導入"""
    logger.info("=== 測試模組導入 ===")
    
    try:
        from jobseeker.ziprecruiter.enhanced_ziprecruiter import EnhancedZipRecruiter
        logger.info("✓ EnhancedZipRecruiter 導入成功")
    except Exception as e:
        logger.error(f"✗ EnhancedZipRecruiter 導入失敗: {e}")
        return False
    
    try:
        from jobseeker.google.enhanced_google import EnhancedGoogle
        logger.info("✓ EnhancedGoogle 導入成功")
    except Exception as e:
        logger.error(f"✗ EnhancedGoogle 導入失敗: {e}")
        return False
    
    try:
        from jobseeker.bayt.enhanced_bayt import EnhancedBaytScraper
        logger.info("✓ EnhancedBaytScraper 導入成功")
    except Exception as e:
        logger.error(f"✗ EnhancedBaytScraper 導入失敗: {e}")
        return False
    
    return True

def test_anti_detection_import():
    """測試反檢測模組的導入"""
    logger.info("=== 測試反檢測模組導入 ===")
    
    try:
        from jobseeker.anti_detection import AntiDetectionScraper
        logger.info("✓ AntiDetectionScraper 導入成功")
        return True
    except Exception as e:
        logger.error(f"✗ AntiDetectionScraper 導入失敗: {e}")
        return False

def test_ziprecruiter():
    """測試 ZipRecruiter 增強版爬蟲"""
    logger.info("=== 測試 ZipRecruiter 增強版爬蟲 ===")
    
    try:
        from jobseeker.ziprecruiter.enhanced_ziprecruiter import EnhancedZipRecruiter
        from jobseeker.model import ScraperInput, Site
        
        # 創建爬蟲實例
        scraper = EnhancedZipRecruiter()
        
        # 創建測試輸入
        scraper_input = ScraperInput(
            site_type=[Site.ZIP_RECRUITER],
            search_term="software engineer",
            location="New York",
            results_wanted=5,
            hours_old=24
        )
        
        logger.info("開始測試 ZipRecruiter 爬取...")
        result = scraper.scrape(scraper_input)
        
        if result and hasattr(result, 'jobs') and len(result.jobs) > 0:
            logger.info(f"✓ ZipRecruiter 測試成功，獲取到 {len(result.jobs)} 個職位")
            return True
        else:
            logger.warning("⚠ ZipRecruiter 測試完成但未獲取到職位數據")
            return False
            
    except Exception as e:
        logger.error(f"✗ ZipRecruiter 測試失敗: {e}")
        logger.error(traceback.format_exc())
        return False

def test_google_jobs():
    """測試 Google Jobs 增強版爬蟲"""
    logger.info("=== 測試 Google Jobs 增強版爬蟲 ===")
    
    try:
        from jobseeker.google.enhanced_google import EnhancedGoogle
        from jobseeker.model import ScraperInput, Site
        
        # 創建爬蟲實例
        scraper = EnhancedGoogle()
        
        # 創建測試輸入
        scraper_input = ScraperInput(
            site_type=[Site.GOOGLE],
            search_term="data scientist",
            location="San Francisco",
            results_wanted=5,
            hours_old=24
        )
        
        logger.info("開始測試 Google Jobs 爬取...")
        result = scraper.scrape(scraper_input)
        
        if result and hasattr(result, 'jobs') and len(result.jobs) > 0:
            logger.info(f"✓ Google Jobs 測試成功，獲取到 {len(result.jobs)} 個職位")
            return True
        else:
            logger.warning("⚠ Google Jobs 測試完成但未獲取到職位數據")
            return False
            
    except Exception as e:
        logger.error(f"✗ Google Jobs 測試失敗: {e}")
        logger.error(traceback.format_exc())
        return False

def test_bayt():
    """測試 Bayt 增強版爬蟲"""
    logger.info("=== 測試 Bayt 增強版爬蟲 ===")
    
    try:
        from jobseeker.bayt.enhanced_bayt import EnhancedBaytScraper
        from jobseeker.model import ScraperInput, Site
        
        # 創建爬蟲實例
        scraper = EnhancedBaytScraper()
        
        # 創建測試輸入
        scraper_input = ScraperInput(
            site_type=[Site.BAYT],
            search_term="software engineer",
            location="Dubai",
            results_wanted=5,
            hours_old=24
        )
        
        logger.info("開始測試 Bayt 爬取...")
        result = scraper.scrape(scraper_input)
        
        if result and hasattr(result, 'jobs') and len(result.jobs) > 0:
            logger.info(f"✓ Bayt 測試成功，獲取到 {len(result.jobs)} 個職位")
            return True
        else:
            logger.warning("⚠ Bayt 測試完成但未獲取到職位數據")
            return False
            
    except Exception as e:
        logger.error(f"✗ Bayt 測試失敗: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主測試函數"""
    logger.info("開始增強版爬蟲最終測試")
    logger.info(f"測試時間: {datetime.now()}")
    
    # 測試結果統計
    results = {
        'imports': False,
        'anti_detection': False,
        'ziprecruiter': False,
        'google': False,
        'bayt': False
    }
    
    # 1. 測試導入
    results['imports'] = test_imports()
    if not results['imports']:
        logger.error("模組導入測試失敗，停止後續測試")
        return results
    
    # 2. 測試反檢測模組
    results['anti_detection'] = test_anti_detection_import()
    
    # 3. 測試各個爬蟲（即使某個失敗也繼續測試其他的）
    logger.info("\n開始功能測試...")
    
    # 測試 ZipRecruiter
    try:
        results['ziprecruiter'] = test_ziprecruiter()
    except Exception as e:
        logger.error(f"ZipRecruiter 測試異常: {e}")
    
    # 測試 Google Jobs
    try:
        results['google'] = test_google_jobs()
    except Exception as e:
        logger.error(f"Google Jobs 測試異常: {e}")
    
    # 測試 Bayt
    try:
        results['bayt'] = test_bayt()
    except Exception as e:
        logger.error(f"Bayt 測試異常: {e}")
    
    # 生成測試報告
    logger.info("\n=== 測試結果總結 ===")
    logger.info(f"模組導入: {'✓' if results['imports'] else '✗'}")
    logger.info(f"反檢測模組: {'✓' if results['anti_detection'] else '✗'}")
    logger.info(f"ZipRecruiter: {'✓' if results['ziprecruiter'] else '✗'}")
    logger.info(f"Google Jobs: {'✓' if results['google'] else '✗'}")
    logger.info(f"Bayt: {'✓' if results['bayt'] else '✗'}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    logger.info(f"\n總體成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    # 運行測試
    try:
        results = main()
        
        # 根據測試結果設置退出碼
        if all(results.values()):
            logger.info("所有測試通過！")
            sys.exit(0)
        else:
            logger.warning("部分測試失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        logger.error(f"測試過程中發生未預期的錯誤: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
