from __future__ import annotations

import os
from typing import Dict, Type

# 增強版爬蟲配置
class EnhancedScraperConfig:
    """
    增強版爬蟲配置管理
    """
    
    # 環境變數控制增強版爬蟲的啟用
    ENABLE_ENHANCED_ZIPRECRUITER = os.getenv('ENABLE_ENHANCED_ZIPRECRUITER', 'true').lower() == 'true'
    ENABLE_ENHANCED_GOOGLE = os.getenv('ENABLE_ENHANCED_GOOGLE', 'true').lower() == 'true'
    ENABLE_ENHANCED_BAYT = os.getenv('ENABLE_ENHANCED_BAYT', 'true').lower() == 'true'
    
    # 全域開關
    ENABLE_ALL_ENHANCED = os.getenv('ENABLE_ALL_ENHANCED', 'true').lower() == 'true'
    
    @classmethod
    def is_enhanced_enabled(cls, site_name: str) -> bool:
        """
        檢查特定網站是否啟用增強版爬蟲
        """
        if not cls.ENABLE_ALL_ENHANCED:
            return False
            
        site_config_map = {
            'ziprecruiter': cls.ENABLE_ENHANCED_ZIPRECRUITER,
            'google': cls.ENABLE_ENHANCED_GOOGLE,
            'bayt': cls.ENABLE_ENHANCED_BAYT,
        }
        
        return site_config_map.get(site_name.lower(), False)
    
    @classmethod
    def get_enhanced_scraper_mapping(cls) -> Dict[str, Type]:
        """
        獲取增強版爬蟲映射
        """
        enhanced_mapping = {}
        
        # 動態導入增強版爬蟲
        if cls.is_enhanced_enabled('ziprecruiter'):
            try:
                from jobspy.ziprecruiter.enhanced_ziprecruiter import EnhancedZipRecruiter
                enhanced_mapping['ziprecruiter'] = EnhancedZipRecruiter
            except ImportError:
                pass
        
        if cls.is_enhanced_enabled('google'):
            try:
                from jobspy.google.enhanced_google import EnhancedGoogle
                enhanced_mapping['google'] = EnhancedGoogle
            except ImportError:
                pass
        
        if cls.is_enhanced_enabled('bayt'):
            try:
                from jobspy.bayt.enhanced_bayt import EnhancedBaytScraper
                enhanced_mapping['bayt'] = EnhancedBaytScraper
            except ImportError:
                pass
        
        return enhanced_mapping
    
    @classmethod
    def log_enhanced_status(cls):
        """
        記錄增強版爬蟲的啟用狀態
        """
        from jobspy.util import create_logger
        log = create_logger("EnhancedConfig")
        
        if not cls.ENABLE_ALL_ENHANCED:
            log.info("增強版爬蟲已全域停用")
            return
        
        enabled_scrapers = []
        if cls.ENABLE_ENHANCED_ZIPRECRUITER:
            enabled_scrapers.append("ZipRecruiter")
        if cls.ENABLE_ENHANCED_GOOGLE:
            enabled_scrapers.append("Google")
        if cls.ENABLE_ENHANCED_BAYT:
            enabled_scrapers.append("Bayt")
        
        if enabled_scrapers:
            log.info(f"已啟用增強版爬蟲: {', '.join(enabled_scrapers)}")
        else:
            log.info("未啟用任何增強版爬蟲")