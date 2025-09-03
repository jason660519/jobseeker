#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化配置管理
提供硬編碼的智能配置，避免複雜的JSON文件

Author: jobseeker Team
Date: 2025-01-27
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PlatformConfig:
    """平台配置"""
    name: str
    priority: int  # 優先級，數字越小優先級越高
    timeout: int   # 超時時間（秒）
    retry_count: int  # 重試次數
    enabled: bool = True  # 是否啟用


class SimpleConfig:
    """簡化配置管理類"""
    
    # 默認配置
    DEFAULT_PLATFORMS = ['indeed', 'linkedin', 'google']
    MAX_CONCURRENT = 3
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 2
    DEFAULT_MAX_RESULTS = 25
    
    # 地區平台映射
    REGION_PLATFORMS = {
        'australia': ['seek', 'indeed', 'linkedin'],
        'usa': ['indeed', 'linkedin', 'ziprecruiter', 'glassdoor'],
        'taiwan': ['104', '1111', 'indeed'],
        'india': ['naukri', 'indeed', 'linkedin'],
        'middle_east': ['bayt', 'indeed', 'linkedin'],
        'bangladesh': ['bdjobs', 'indeed'],
        'global': DEFAULT_PLATFORMS
    }
    
    # 地理位置關鍵詞映射
    LOCATION_KEYWORDS = {
        'australia': [
            'australia', '澳洲', '澳大利亞', 'oz', 'aussie',
            'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
            'canberra', 'darwin', 'hobart', 'gold coast', 'newcastle',
            'nsw', 'vic', 'qld', 'wa', 'sa', 'tas', 'act', 'nt'
        ],
        'usa': [
            'usa', 'america', 'united states', 'us', 'states',
            'new york', 'california', 'texas', 'florida', 'illinois',
            'pennsylvania', 'ohio', 'georgia', 'north carolina', 'michigan',
            'ny', 'ca', 'tx', 'fl', 'il', 'pa', 'oh', 'ga', 'nc', 'mi'
        ],
        'taiwan': [
            'taiwan', '台灣', '中華民國', 'tw', 'roc',
            'taipei', '台北', 'taichung', '台中', 'tainan', '台南',
            'kaohsiung', '高雄', 'hsinchu', '新竹', 'keelung', '基隆',
            'new taipei', '新北', 'taoyuan', '桃園'
        ],
        'india': [
            'india', '印度', 'in', 'bharat',
            'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai',
            'kolkata', 'pune', 'ahmedabad', 'jaipur', 'surat',
            'maharashtra', 'karnataka', 'tamil nadu', 'west bengal'
        ],
        'middle_east': [
            'dubai', 'uae', 'saudi', 'saudi arabia', 'qatar', 'kuwait',
            'bahrain', 'oman', 'jordan', 'lebanon', 'egypt',
            'abu dhabi', 'riyadh', 'doha', 'manama', 'muscat',
            '中東', '阿拉伯', '海灣'
        ],
        'bangladesh': [
            'bangladesh', '孟加拉', 'bd', 'dhaka', 'chittagong',
            'sylhet', 'rajshahi', 'khulna', 'barisal', 'rangpur'
        ]
    }
    
    # 平台詳細配置
    PLATFORM_CONFIGS = {
        'indeed': PlatformConfig('indeed', 1, 60, 2),
        'linkedin': PlatformConfig('linkedin', 2, 90, 2),
        'google': PlatformConfig('google', 3, 30, 1),
        'seek': PlatformConfig('seek', 1, 45, 3),
        'ziprecruiter': PlatformConfig('ziprecruiter', 3, 50, 2),
        'glassdoor': PlatformConfig('glassdoor', 4, 75, 1),
        '104': PlatformConfig('104', 1, 40, 2),
        '1111': PlatformConfig('1111', 2, 40, 2),
        'naukri': PlatformConfig('naukri', 1, 50, 2),
        'bayt': PlatformConfig('bayt', 2, 60, 2),
        'bdjobs': PlatformConfig('bdjobs', 1, 45, 2)
    }
    
    @classmethod
    def get_platforms_for_region(cls, region: str) -> List[str]:
        """
        根據地區獲取推薦平台
        
        Args:
            region: 地區名稱
            
        Returns:
            平台名稱列表
        """
        return cls.REGION_PLATFORMS.get(region, cls.DEFAULT_PLATFORMS)
    
    @classmethod
    def detect_region(cls, text: str) -> Optional[str]:
        """
        從文本中檢測地區
        
        Args:
            text: 輸入文本
            
        Returns:
            檢測到的地區名稱，如果未檢測到則返回None
        """
        text_lower = text.lower()
        
        for region, keywords in cls.LOCATION_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return region
        
        return None
    
    @classmethod
    def get_platform_config(cls, platform_name: str) -> Optional[PlatformConfig]:
        """
        獲取平台配置
        
        Args:
            platform_name: 平台名稱
            
        Returns:
            平台配置對象
        """
        return cls.PLATFORM_CONFIGS.get(platform_name)
    
    @classmethod
    def get_enabled_platforms(cls) -> List[str]:
        """
        獲取所有啟用的平台
        
        Returns:
            啟用的平台名稱列表
        """
        return [
            config.name for config in cls.PLATFORM_CONFIGS.values()
            if config.enabled
        ]
    
    @classmethod
    def sort_platforms_by_priority(cls, platforms: List[str]) -> List[str]:
        """
        根據優先級排序平台
        
        Args:
            platforms: 平台名稱列表
            
        Returns:
            按優先級排序的平台列表
        """
        def get_priority(platform_name: str) -> int:
            config = cls.get_platform_config(platform_name)
            return config.priority if config else 999
        
        return sorted(platforms, key=get_priority)
    
    @classmethod
    def validate_platforms(cls, platforms: List[str]) -> List[str]:
        """
        驗證並過濾平台列表
        
        Args:
            platforms: 平台名稱列表
            
        Returns:
            有效的平台名稱列表
        """
        enabled_platforms = cls.get_enabled_platforms()
        return [p for p in platforms if p in enabled_platforms]


# 全局配置實例
config = SimpleConfig()
