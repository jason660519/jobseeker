#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 智能路由系統
根據用戶查詢自動選擇最適合的爬蟲代理

功能:
1. 地理位置檢測和分析
2. 關鍵詞提取和分類
3. 智能代理選擇
4. 動態路由決策

Author: jobseeker Team
Date: 2025-01-27
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """代理類型枚舉"""
    SEEK = "seek"  # 澳洲專業
    INDEED = "indeed"  # 全球通用
    LINKEDIN = "linkedin"  # 全球專業網路
    GLASSDOOR = "glassdoor"  # 薪資和公司評價
    ZIPRECRUITER = "ziprecruiter"  # 美國專業
    NAUKRI = "naukri"  # 印度專業
    BAYT = "bayt"  # 中東專業
    BDJOBS = "bdjobs"  # 孟加拉專業
    GOOGLE = "google"  # 全球聚合
    T104 = "104"  # 台灣 104 人力銀行
    JOB1111 = "1111"  # 台灣 1111 人力銀行

@dataclass
class GeographicRegion:
    """地理區域定義"""
    name: str
    countries: List[str]
    states_provinces: List[str]
    cities: List[str]
    keywords: List[str]
    primary_agents: List[AgentType]
    secondary_agents: List[AgentType]

@dataclass
class IndustryCategory:
    """行業分類定義"""
    name: str
    keywords: List[str]
    preferred_agents: List[AgentType]
    weight: float

@dataclass
class RoutingDecision:
    """路由決策結果"""
    selected_agents: List[AgentType]
    confidence_score: float
    reasoning: str
    geographic_match: Optional[str]
    industry_match: Optional[str]
    fallback_agents: List[AgentType]

class IntelligentRouter:
    """智能路由器主類"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化智能路由器
        
        Args:
            config_path: 配置文件路徑
        """
        self.geographic_regions = self._load_geographic_regions()
        self.industry_categories = self._load_industry_categories()
        self.agent_capabilities = self._load_agent_capabilities()
        
        if config_path:
            self._load_custom_config(config_path)
    
    def _load_geographic_regions(self) -> List[GeographicRegion]:
        """
        載入地理區域配置
        
        Returns:
            地理區域列表
        """
        return [
            # 澳洲和紐西蘭
            GeographicRegion(
                name="Australia_NewZealand",
                countries=["australia", "new zealand", "澳洲", "澳大利亞", "紐西蘭"],
                states_provinces=[
                    "nsw", "new south wales", "vic", "victoria", "qld", "queensland",
                    "wa", "western australia", "sa", "south australia", "tas", "tasmania",
                    "act", "nt", "northern territory"
                ],
                cities=[
                    "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra",
                    "darwin", "hobart", "gold coast", "newcastle", "wollongong",
                    "gledswood hill", "campbelltown", "penrith", "parramatta"
                ],
                keywords=["澳洲", "australia", "aussie", "oz", "aud", "kilometre", "km"],
                primary_agents=[AgentType.SEEK],
                secondary_agents=[AgentType.INDEED, AgentType.LINKEDIN, AgentType.GOOGLE]
            ),
            
            # 美國和加拿大
            GeographicRegion(
                name="North_America",
                countries=["usa", "united states", "america", "canada", "美國", "加拿大", "美国"],
                states_provinces=[
                    "california", "new york", "ny", "texas", "florida", "illinois",
                    "ontario", "quebec", "british columbia", "alberta", "紐約州", "加州"
                ],
                cities=[
                    "new york", "nyc", "紐約", "纽约", "los angeles", "chicago", "houston", "phoenix",
                    "toronto", "vancouver", "montreal", "calgary", "manhattan", "brooklyn",
                    "洛杉磯", "芝加哥", "多倫多", "溫哥華"
                ],
                keywords=["美國", "美国", "usa", "usd", "mile", "miles", "州", "state", "america", "北美"],
                primary_agents=[AgentType.INDEED, AgentType.ZIPRECRUITER],
                secondary_agents=[AgentType.LINKEDIN, AgentType.GOOGLE]
            ),
            
            # 印度
            GeographicRegion(
                name="India",
                countries=["india", "印度"],
                states_provinces=[
                    "maharashtra", "karnataka", "tamil nadu", "delhi", "gujarat",
                    "west bengal", "rajasthan", "andhra pradesh"
                ],
                cities=[
                    "mumbai", "bangalore", "delhi", "hyderabad", "chennai",
                    "pune", "kolkata", "ahmedabad", "gurgaon", "noida"
                ],
                keywords=["印度", "india", "inr", "rupee", "lakh", "crore"],
                primary_agents=[AgentType.NAUKRI],
                secondary_agents=[AgentType.INDEED, AgentType.LINKEDIN, AgentType.GOOGLE]
            ),
            
            # 中東
            GeographicRegion(
                name="Middle_East",
                countries=[
                    "uae", "united arab emirates", "saudi arabia", "qatar", "kuwait", "bahrain", "oman",
                    "阿聯酋", "阿拉伯聯合大公國", "沙烏地阿拉伯", "沙特阿拉伯", "卡達", "科威特", 
                    "巴林", "阿曼", "emirates", "saudi", "emirates"
                ],
                states_provinces=[
                    "dubai", "abu dhabi", "riyadh", "jeddah", "doha", "sharjah", 
                    "杜拜", "阿布達比", "利雅德", "吉達", "多哈", "沙迦"
                ],
                cities=[
                    "dubai", "abu dhabi", "riyadh", "jeddah", "doha", "kuwait city",
                    "manama", "muscat", "sharjah", "al ain", "fujairah",
                    "杜拜", "阿布達比", "利雅德", "吉達", "多哈", "科威特城",
                    "麥納麥", "馬斯喀特", "沙迦", "艾因", "富查伊拉"
                ],
                keywords=[
                    "中東", "gulf", "gcc", "aed", "sar", "qar", "arabic", "middle east",
                    "海灣", "波斯灣", "阿拉伯", "emirates", "杜拜", "dubai", "阿聯酋", "uae"
                ],
                primary_agents=[AgentType.BAYT],
                secondary_agents=[AgentType.INDEED, AgentType.LINKEDIN, AgentType.GOOGLE]
            ),
            
            # 孟加拉
            GeographicRegion(
                name="Bangladesh",
                countries=["bangladesh", "孟加拉"],
                states_provinces=["dhaka", "chittagong", "sylhet", "rajshahi"],
                cities=["dhaka", "chittagong", "sylhet", "rajshahi", "khulna"],
                keywords=["孟加拉", "bangladesh", "bdt", "taka"],
                primary_agents=[AgentType.BDJOBS],
                secondary_agents=[AgentType.INDEED, AgentType.LINKEDIN, AgentType.GOOGLE]
            ),
            
            # 東南亞
            GeographicRegion(
                name="Southeast_Asia",
                countries=[
                    "singapore", "malaysia", "thailand", "indonesia", "philippines", 
                    "vietnam", "taiwan", "japan", "新加坡", "馬來西亞", "泰國", "印尼", 
                    "菲律賓", "越南", "台灣", "日本", "臺灣"
                ],
                states_provinces=[
                    "kuala lumpur", "selangor", "penang", "johor", "bangkok", 
                    "jakarta", "manila", "ho chi minh", "hanoi", "taipei", "tokyo",
                    "台北", "東京", "臺北"
                ],
                cities=[
                    "singapore", "新加坡", "kuala lumpur", "bangkok", "jakarta", 
                    "manila", "ho chi minh city", "hanoi", "penang", "johor bahru",
                    "taipei", "tokyo", "台北", "東京", "臺北", "大阪", "osaka",
                    "首都", "capital", "city center", "downtown"
                ],
                keywords=[
                    "東南亞", "southeast asia", "asean", "sgd", "myr", "thb", 
                    "idr", "php", "vnd", "twd", "jpy", "新加坡", "singapore", 
                    "台灣", "taiwan", "臺灣", "日本", "japan", "首都", "asia", "亞洲"
                ],
                primary_agents=[AgentType.INDEED, AgentType.LINKEDIN],
                secondary_agents=[AgentType.GOOGLE]
            ),

            # 台灣（專門區域，偏好在地平台）
            GeographicRegion(
                name="Taiwan",
                countries=["taiwan", "台灣", "臺灣"],
                states_provinces=["taipei", "台北", "新北", "台中", "台南", "高雄", "桃園", "新竹"],
                cities=["taipei", "台北", "新北", "台中", "台南", "高雄", "桃園", "新竹"],
                keywords=["台灣", "臺灣", "taiwan", "ntd", "twd"],
                primary_agents=[AgentType.T104, AgentType.JOB1111],
                secondary_agents=[AgentType.LINKEDIN, AgentType.INDEED, AgentType.GOOGLE]
            ),
            
            # 歐洲
            GeographicRegion(
                name="Europe",
                countries=[
                    "united kingdom", "uk", "britain", "england", "scotland", "wales", "northern ireland",
                    "france", "germany", "deutschland", "netherlands", "belgium", "switzerland",
                    "austria", "italy", "spain", "portugal", "sweden", "norway", "denmark",
                    "finland", "poland", "czech republic", "hungary", "romania", "bulgaria",
                    "英國", "法國", "德國", "荷蘭", "比利時", "瑞士", "奧地利", "義大利",
                    "西班牙", "葡萄牙", "瑞典", "挪威", "丹麥", "芬蘭", "波蘭", "捷克",
                    "匈牙利", "羅馬尼亞", "保加利亞", "歐洲", "europe"
                ],
                states_provinces=[
                    "london", "manchester", "birmingham", "glasgow", "edinburgh", "cardiff", "belfast",
                    "paris", "lyon", "marseille", "toulouse", "nice", "nantes", "strasbourg",
                    "berlin", "munich", "hamburg", "cologne", "frankfurt", "stuttgart", "düsseldorf",
                    "amsterdam", "rotterdam", "the hague", "utrecht", "eindhoven",
                    "brussels", "antwerp", "ghent", "bruges", "zurich", "geneva", "basel",
                    "倫敦", "曼徹斯特", "伯明翰", "格拉斯哥", "愛丁堡", "卡迪夫", "貝爾法斯特",
                    "巴黎", "里昂", "馬賽", "圖盧茲", "尼斯", "南特", "史特拉斯堡",
                    "柏林", "慕尼黑", "漢堡", "科隆", "法蘭克福", "斯圖加特", "杜塞道夫"
                ],
                cities=[
                    "london", "manchester", "birmingham", "liverpool", "leeds", "sheffield", "bristol",
                    "glasgow", "edinburgh", "cardiff", "belfast", "oxford", "cambridge", "brighton",
                    "paris", "lyon", "marseille", "toulouse", "nice", "nantes", "strasbourg", "bordeaux",
                    "berlin", "munich", "hamburg", "cologne", "frankfurt", "stuttgart", "düsseldorf", "dortmund",
                    "amsterdam", "rotterdam", "the hague", "utrecht", "eindhoven", "tilburg",
                    "brussels", "antwerp", "ghent", "bruges", "leuven",
                    "zurich", "geneva", "basel", "bern", "lausanne",
                    "倫敦", "曼徹斯特", "伯明翰", "利物浦", "里茲", "謝菲爾德", "布里斯托",
                    "格拉斯哥", "愛丁堡", "卡迪夫", "貝爾法斯特", "牛津", "劍橋", "布萊頓",
                    "巴黎", "里昂", "馬賽", "圖盧茲", "尼斯", "南特", "史特拉斯堡", "波爾多",
                    "柏林", "慕尼黑", "漢堡", "科隆", "法蘭克福", "斯圖加特", "杜塞道夫", "多特蒙德",
                    "阿姆斯特丹", "鹿特丹", "海牙", "烏特勒支", "埃因霍溫",
                    "布魯塞爾", "安特衛普", "根特", "布魯日",
                    "蘇黎世", "日內瓦", "巴塞爾", "伯恩", "洛桑"
                ],
                keywords=[
                    "歐洲", "europe", "european", "eu", "eur", "euro", "pound", "gbp", "sterling",
                    "英國", "uk", "britain", "british", "england", "english", "london",
                    "法國", "france", "french", "paris", "français",
                    "德國", "germany", "german", "deutsch", "berlin", "münchen",
                    "荷蘭", "netherlands", "dutch", "holland", "amsterdam",
                    "比利時", "belgium", "belgian", "brussels", "flemish",
                    "瑞士", "switzerland", "swiss", "zurich", "geneva",
                    "歐盟", "european union", "schengen", "eurozone", "首都", "capital"
                ],
                primary_agents=[AgentType.INDEED, AgentType.LINKEDIN],
                secondary_agents=[AgentType.GOOGLE]
            )
        ]
    
    def _load_industry_categories(self) -> List[IndustryCategory]:
        """
        載入行業分類配置
        
        Returns:
            行業分類列表
        """
        return [
            IndustryCategory(
                name="Technology",
                keywords=[
                    "software", "developer", "engineer", "programming", "coding",
                    "python", "java", "javascript", "react", "node.js", "ai", "ml",
                    "data scientist", "devops", "cloud", "aws", "azure", "技術", "工程師",
                    "程式設計", "軟體", "開發", "人工智慧", "機器學習"
                ],
                preferred_agents=[AgentType.LINKEDIN, AgentType.INDEED],
                weight=1.2
            ),
            
            IndustryCategory(
                name="Construction",
                keywords=[
                    "construction", "building", "architect", "civil engineer", "project manager",
                    "site supervisor", "foreman", "carpenter", "electrician", "plumber",
                    "建築", "建設", "工程", "建築師", "土木工程師", "工地", "施工"
                ],
                preferred_agents=[AgentType.SEEK, AgentType.INDEED],  # SEEK 在澳洲建築業很強
                weight=1.1
            ),
            
            IndustryCategory(
                name="Healthcare",
                keywords=[
                    "doctor", "nurse", "medical", "healthcare", "hospital", "clinic",
                    "physician", "surgeon", "pharmacist", "therapist", "醫療", "醫生",
                    "護士", "醫院", "診所", "藥師", "治療師"
                ],
                preferred_agents=[AgentType.INDEED, AgentType.LINKEDIN],
                weight=1.0
            ),
            
            IndustryCategory(
                name="Finance",
                keywords=[
                    "finance", "banking", "accountant", "accounting", "financial analyst", "investment",
                    "insurance", "audit", "tax", "cpa", "bookkeeper", "金融", "銀行", "會計", "投資",
                    "保險", "審計", "稅務", "記帳"
                ],
                preferred_agents=[AgentType.LINKEDIN, AgentType.INDEED],
                weight=1.1
            ),
            
            IndustryCategory(
                name="Education",
                keywords=[
                    "teacher", "professor", "education", "school", "university", "tutor",
                    "instructor", "academic", "research", "教育", "老師", "教授", "學校",
                    "大學", "研究", "學術"
                ],
                preferred_agents=[AgentType.INDEED, AgentType.LINKEDIN],
                weight=1.0
            ),
            
            IndustryCategory(
                name="Sales_Marketing",
                keywords=[
                    "sales", "marketing", "business development", "account manager",
                    "digital marketing", "seo", "social media", "advertising",
                    "銷售", "行銷", "業務", "客戶經理", "數位行銷", "廣告"
                ],
                preferred_agents=[AgentType.LINKEDIN, AgentType.INDEED],
                weight=1.0
            )
        ]
    
    def _load_agent_capabilities(self) -> Dict[AgentType, Dict]:
        """
        載入代理能力配置
        
        Returns:
            代理能力字典
        """
        return {
            AgentType.SEEK: {
                "regions": ["Australia", "New Zealand"],
                "strengths": ["local_jobs", "construction", "trades", "government"],
                "reliability": 0.9,
                "coverage": "high_local",
                "languages": ["en"]
            },
            
            AgentType.INDEED: {
                "regions": ["Global"],
                "strengths": ["volume", "variety", "entry_level", "mid_level"],
                "reliability": 0.85,
                "coverage": "high_global",
                "languages": ["en", "es", "fr", "de", "it"]
            },
            
            AgentType.LINKEDIN: {
                "regions": ["Global"],
                "strengths": ["professional", "senior_level", "networking", "tech"],
                "reliability": 0.88,
                "coverage": "medium_global",
                "languages": ["en", "es", "fr", "de", "it", "pt", "zh"]
            },
            
            AgentType.GLASSDOOR: {
                "regions": ["US", "Canada", "UK", "Germany"],
                "strengths": ["salary_info", "company_reviews", "senior_level"],
                "reliability": 0.82,
                "coverage": "medium_selective",
                "languages": ["en", "de"]
            },
            
            AgentType.ZIPRECRUITER: {
                "regions": ["US", "Canada"],
                "strengths": ["quick_apply", "local_us", "volume"],
                "reliability": 0.80,
                "coverage": "high_us",
                "languages": ["en"]
            },
            
            AgentType.NAUKRI: {
                "regions": ["India"],
                "strengths": ["local_india", "tech", "volume", "fresher"],
                "reliability": 0.87,
                "coverage": "high_india",
                "languages": ["en", "hi"]
            },
            
            AgentType.BAYT: {
                "regions": ["Middle East", "North Africa"],
                "strengths": ["local_mena", "arabic", "oil_gas", "finance"],
                "reliability": 0.83,
                "coverage": "high_mena",
                "languages": ["en", "ar"]
            },
            
            AgentType.BDJOBS: {
                "regions": ["Bangladesh"],
                "strengths": ["local_bangladesh", "entry_level", "volume"],
                "reliability": 0.78,
                "coverage": "high_bangladesh",
                "languages": ["en", "bn"]
            },
            
            AgentType.GOOGLE: {
                "regions": ["Global"],
                "strengths": ["aggregation", "comprehensive", "discovery"],
                "reliability": 0.75,
                "coverage": "high_global",
                "languages": ["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"]
            }
        }
    
    def analyze_query(self, query: str) -> RoutingDecision:
        """
        分析用戶查詢並做出路由決策
        
        Args:
            query: 用戶查詢字符串
            
        Returns:
            路由決策結果
        """
        logger.info(f"分析查詢: {query}")
        
        # 1. 地理位置檢測
        geographic_match = self._detect_geography(query)
        
        # 2. 行業分類檢測
        industry_match = self._detect_industry(query)
        
        # 3. 距離和範圍檢測
        distance_info = self._detect_distance(query)
        
        # 4. 語言檢測
        language = self._detect_language(query)
        
        # 5. 生成路由決策
        decision = self._make_routing_decision(
            geographic_match, industry_match, distance_info, language, query
        )
        
        logger.info(f"路由決策: {decision.selected_agents}, 信心度: {decision.confidence_score}")
        return decision
    
    def _detect_geography(self, query: str) -> Optional[GeographicRegion]:
        """
        檢測查詢中的地理位置
        
        Args:
            query: 查詢字符串
            
        Returns:
            匹配的地理區域
        """
        query_lower = query.lower()
        logger.info(f"地理檢測 - 查詢字符串: {query_lower}")
        
        # 優先檢查完整的地理名稱，避免短縮寫造成誤判
        best_match = None
        best_match_length = 0
        
        for region in self.geographic_regions:
            logger.info(f"檢查區域: {region.name}")
            # 檢查國家 - 使用詞邊界匹配
            for country in region.countries:
                country_lower = country.lower()
                logger.info(f"檢查國家: {country_lower}")
                if len(country_lower) >= 3:  # 避免過短的匹配
                    if re.search(r'\b' + re.escape(country_lower) + r'\b', query_lower):
                        if len(country_lower) > best_match_length:
                            best_match = region
                            best_match_length = len(country_lower)
                            logger.info(f"檢測到國家: {country} -> 區域: {region.name}")
                elif country_lower in query_lower:  # 對於中文，使用包含匹配
                    if len(country_lower) > best_match_length:
                        best_match = region
                        best_match_length = len(country_lower)
                        logger.info(f"檢測到國家(包含匹配): {country} -> 區域: {region.name}")
            
            # 檢查州省 - 使用更嚴格的匹配
            for state in region.states_provinces:
                state_lower = state.lower()
                # 對於短縮寫，需要更精確的匹配
                if len(state_lower) <= 3:
                    # 短縮寫需要詞邊界或特定上下文
                    pattern = r'\b' + re.escape(state_lower) + r'\b'
                    if re.search(pattern, query_lower):
                        # 額外檢查：確保不是其他詞的一部分
                        if self._validate_state_match(query_lower, state_lower, region.name):
                            if len(state_lower) > best_match_length:
                                best_match = region
                                best_match_length = len(state_lower)
                                logger.info(f"檢測到州省: {state} -> 區域: {region.name}")
                else:
                    # 長名稱使用包含匹配
                    if state_lower in query_lower:
                        if len(state_lower) > best_match_length:
                            best_match = region
                            best_match_length = len(state_lower)
                            logger.info(f"檢測到州省: {state} -> 區域: {region.name}")
            
            # 檢查城市
            for city in region.cities:
                city_lower = city.lower()
                if len(city_lower) >= 3:  # 避免過短的城市名稱匹配
                    if re.search(r'\b' + re.escape(city_lower) + r'\b', query_lower):
                        if len(city_lower) > best_match_length:
                            best_match = region
                            best_match_length = len(city_lower)
                            logger.info(f"檢測到城市: {city} -> 區域: {region.name}")
            
            # 檢查關鍵詞
            for keyword in region.keywords:
                keyword_lower = keyword.lower()
                if len(keyword_lower) >= 3:
                    if keyword_lower in query_lower:
                        if len(keyword_lower) > best_match_length:
                            best_match = region
                            best_match_length = len(keyword_lower)
                            logger.info(f"檢測到地理關鍵詞: {keyword} -> 區域: {region.name}")
        
        return best_match
    
    def _validate_state_match(self, query: str, state_abbr: str, region_name: str) -> bool:
        """
        驗證州省縮寫匹配的有效性
        
        Args:
            query: 查詢字符串
            state_abbr: 州省縮寫
            region_name: 區域名稱
            
        Returns:
            是否為有效匹配
        """
        # 特殊處理：避免 NY (紐約) 被誤認為 NT (北領地)
        if state_abbr == "nt" and "紐約" in query:
            return False
        if state_abbr == "nt" and "new york" in query:
            return False
        if state_abbr == "nt" and "ny" in query and ("美國" in query or "usa" in query or "united states" in query):
            return False
            
        # 特殊處理：確保 NSW 不會與其他地區混淆
        if state_abbr == "nsw" and region_name != "Australia_NewZealand":
            return False
            
        return True
    
    def _detect_industry(self, query: str) -> Optional[IndustryCategory]:
        """
        檢測查詢中的行業類別
        
        Args:
            query: 查詢字符串
            
        Returns:
            匹配的行業類別
        """
        query_lower = query.lower()
        best_match = None
        max_matches = 0
        
        for industry in self.industry_categories:
            matches = 0
            for keyword in industry.keywords:
                if keyword.lower() in query_lower:
                    matches += 1
            
            if matches > max_matches:
                max_matches = matches
                best_match = industry
        
        if best_match:
            logger.info(f"檢測到行業: {best_match.name} (匹配 {max_matches} 個關鍵詞)")
        
        return best_match
    
    def _detect_distance(self, query: str) -> Dict[str, any]:
        """
        檢測查詢中的距離和範圍信息
        
        Args:
            query: 查詢字符串
            
        Returns:
            距離信息字典
        """
        distance_patterns = [
            r'(\d+)\s*(km|kilometre|kilometer|公里)',
            r'(\d+)\s*(mile|miles|英里)',
            r'within\s+(\d+)\s*(km|mile)',
            r'(\d+)\s*公里內',
            r'方圓\s*(\d+)\s*(公里|km)'
        ]
        
        for pattern in distance_patterns:
            match = re.search(pattern, query.lower())
            if match:
                distance = int(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 else 'km'
                
                # 轉換為公里
                if 'mile' in unit or '英里' in unit:
                    distance_km = distance * 1.609
                else:
                    distance_km = distance
                
                logger.info(f"檢測到距離: {distance} {unit} ({distance_km:.1f} km)")
                return {
                    'distance': distance,
                    'unit': unit,
                    'distance_km': distance_km,
                    'is_local_search': distance_km <= 100
                }
        
        return {'is_local_search': False}
    
    def _detect_language(self, query: str) -> str:
        """
        檢測查詢語言
        
        Args:
            query: 查詢字符串
            
        Returns:
            語言代碼
        """
        # 簡單的語言檢測
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', query)
        if len(chinese_chars) > len(query) * 0.3:
            return 'zh'
        
        arabic_chars = re.findall(r'[\u0600-\u06ff]', query)
        if len(arabic_chars) > 0:
            return 'ar'
        
        return 'en'
    
    def _make_routing_decision(
        self, 
        geographic_match: Optional[GeographicRegion],
        industry_match: Optional[IndustryCategory],
        distance_info: Dict,
        language: str,
        original_query: str
    ) -> RoutingDecision:
        """
        基於分析結果做出路由決策
        
        Args:
            geographic_match: 地理匹配結果
            industry_match: 行業匹配結果
            distance_info: 距離信息
            language: 語言
            original_query: 原始查詢
            
        Returns:
            路由決策
        """
        selected_agents = set()
        reasoning_parts = []
        confidence_score = 0.5  # 基礎信心度
        
        # 1. 基於地理位置選擇代理
        if geographic_match:
            selected_agents.update(geographic_match.primary_agents)
            selected_agents.update(geographic_match.secondary_agents)
            reasoning_parts.append(f"地理位置匹配: {geographic_match.name}")
            confidence_score += 0.3
        
        # 2. 基於行業選擇代理
        if industry_match:
            selected_agents.update(industry_match.preferred_agents)
            reasoning_parts.append(f"行業匹配: {industry_match.name}")
            confidence_score += 0.2 * industry_match.weight
        
        # 3. 基於距離調整
        if distance_info.get('is_local_search', False):
            # 本地搜索優先選擇地區性代理
            if geographic_match:
                # 提高主要代理的優先級
                primary_agents = set(geographic_match.primary_agents)
                selected_agents = primary_agents.union(selected_agents)
                reasoning_parts.append(f"本地搜索 ({distance_info.get('distance_km', 0):.1f}km)")
                confidence_score += 0.1
        
        # 4. 如果沒有地理匹配，使用更全面的全球代理
        if not geographic_match:
            global_agents = [
                AgentType.INDEED, 
                AgentType.LINKEDIN, 
                AgentType.GOOGLE,
                AgentType.ZIPRECRUITER,
                AgentType.SEEK,
                AgentType.T104,
                AgentType.JOB1111
            ]
            selected_agents.update(global_agents)
            reasoning_parts.append("使用全面全球代理（包含地區性平台）")
        
        # 5. Glassdoor 地區限制檢查
        if AgentType.GLASSDOOR in selected_agents:
            # 檢查是否為全球查詢或無具體地理位置
            is_worldwide_query = (
                not geographic_match or 
                'worldwide' in original_query.lower() or
                (not geographic_match and not distance_info.get('is_local_search', False))
            )
            
            if is_worldwide_query:
                selected_agents.discard(AgentType.GLASSDOOR)
                reasoning_parts.append("排除 Glassdoor（不支援全球查詢）")
        
        # 6. 確保至少有一些代理被選中
        if not selected_agents:
            selected_agents = {
                AgentType.INDEED, 
                AgentType.LINKEDIN, 
                AgentType.GOOGLE,
                AgentType.ZIPRECRUITER,
                AgentType.SEEK,
                AgentType.T104,
                AgentType.JOB1111
            }
            reasoning_parts.append("默認全面代理選擇")
        
        # 7. 基於代理可靠性排序
        sorted_agents = self._sort_agents_by_reliability(list(selected_agents))
        
        # 8. 設置後備代理（排除 Glassdoor）
        fallback_agents = [AgentType.INDEED, AgentType.GOOGLE]
        if geographic_match:
            # 只添加非 Glassdoor 的後備代理
            for agent in geographic_match.secondary_agents:
                if agent != AgentType.GLASSDOOR:
                    fallback_agents.append(agent)
        
        # 9. 限制代理數量（避免過多並發請求）
        max_agents = 6  # 增加最大代理數量
        if len(sorted_agents) > max_agents:
            sorted_agents = sorted_agents[:max_agents]
            reasoning_parts.append(f"限制為前 {max_agents} 個代理")
        
        reasoning = "; ".join(reasoning_parts)
        
        return RoutingDecision(
            selected_agents=sorted_agents,
            confidence_score=min(confidence_score, 1.0),
            reasoning=reasoning,
            geographic_match=geographic_match.name if geographic_match else None,
            industry_match=industry_match.name if industry_match else None,
            fallback_agents=fallback_agents
        )
    
    def _sort_agents_by_reliability(self, agents: List[AgentType]) -> List[AgentType]:
        """
        根據可靠性對代理進行排序
        
        Args:
            agents: 代理列表
            
        Returns:
            排序後的代理列表
        """
        return sorted(
            agents, 
            key=lambda agent: self.agent_capabilities.get(agent, {}).get('reliability', 0.5),
            reverse=True
        )
    
    def get_routing_explanation(self, decision: RoutingDecision) -> str:
        """
        獲取路由決策的詳細解釋
        
        Args:
            decision: 路由決策
            
        Returns:
            詳細解釋字符串
        """
        explanation = f"""智能路由決策報告
========================

選中的代理: {[agent.value for agent in decision.selected_agents]}
信心度: {decision.confidence_score:.2f}

決策理由: {decision.reasoning}

地理匹配: {decision.geographic_match or '無'}
行業匹配: {decision.industry_match or '無'}

代理詳情:
"""
        
        for agent in decision.selected_agents:
            capabilities = self.agent_capabilities.get(agent, {})
            explanation += f"""
- {agent.value.upper()}:
  可靠性: {capabilities.get('reliability', 'N/A')}
  覆蓋範圍: {capabilities.get('coverage', 'N/A')}
  強項: {', '.join(capabilities.get('strengths', []))}
"""
        
        if decision.fallback_agents:
            explanation += f"""
後備代理: {[agent.value for agent in decision.fallback_agents]}
"""
        
        return explanation
    
    def _load_custom_config(self, config_path: str):
        """
        載入自定義配置
        
        Args:
            config_path: 配置文件路徑
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新配置
            if 'geographic_regions' in config:
                # 合併自定義地理區域
                pass
            
            if 'industry_categories' in config:
                # 合併自定義行業分類
                pass
                
            logger.info(f"已載入自定義配置: {config_path}")
            
        except Exception as e:
            logger.warning(f"載入自定義配置失敗: {e}")


def demo_routing_system():
    """
    演示智能路由系統
    """
    router = IntelligentRouter()
    
    # 測試案例
    test_queries = [
        "請你幫我找Australia NSW Gledswood Hill 50公里內有關建築行業的工作",
        "Looking for software engineer jobs in San Francisco Bay Area",
        "Find marketing manager positions in Mumbai, India",
        "Search for finance jobs in Dubai, UAE within 25km",
        "需要在台北找資料科學家的工作",
        "Looking for nursing jobs in Toronto, Canada",
        "Find construction project manager jobs in Sydney"
    ]
    
    print("=" * 60)
    print("jobseeker 智能路由系統演示")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n測試案例 {i}: {query}")
        print("-" * 50)
        
        decision = router.analyze_query(query)
        
        print(f"選中代理: {[agent.value for agent in decision.selected_agents]}")
        print(f"信心度: {decision.confidence_score:.2f}")
        print(f"決策理由: {decision.reasoning}")
        
        if decision.geographic_match:
            print(f"地理匹配: {decision.geographic_match}")
        
        if decision.industry_match:
            print(f"行業匹配: {decision.industry_match}")


if __name__ == "__main__":
    demo_routing_system()
