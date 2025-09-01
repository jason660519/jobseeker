#!/usr/bin/env python3
"""
反檢測核心模組 - 高級反反爬蟲解決方案
提供 User-Agent 池、代理管理、瀏覽器指紋偽裝等功能
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
# from fake_useragent import UserAgent  # 暫時註解掉以避免導入問題
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrowserProfile:
    """瀏覽器配置文件"""
    user_agent: str
    viewport: Dict[str, int]
    locale: str
    timezone: str
    platform: str
    screen: Dict[str, int]

class UserAgentPool:
    """User-Agent 池管理器"""
    
    def __init__(self):
        """初始化 User-Agent 池"""
        self.custom_agents = [
            # Windows Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Windows Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # macOS Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            # macOS Chrome
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    def get_random_agent(self) -> str:
        """獲取隨機 User-Agent"""
        return random.choice(self.custom_agents)

class ProxyManager:
    """代理管理器"""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        """初始化代理管理器"""
        self.proxy_list = proxy_list or []
        self.current_index = 0
    
    def get_next_proxy(self) -> Optional[str]:
        """獲取下一個代理"""
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy
    
    def add_proxy(self, proxy: str):
        """添加代理"""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)

class BrowserProfileGenerator:
    """瀏覽器配置文件生成器"""
    
    def __init__(self):
        """初始化配置文件生成器"""
        self.ua_pool = UserAgentPool()
        
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1280, "height": 720},
        ]
        
        self.locales = [
            "en-US", "en-GB", "zh-CN", "zh-TW", "ja-JP", "ko-KR"
        ]
        
        self.timezones = [
            "America/New_York", "America/Los_Angeles", "Europe/London",
            "Asia/Shanghai", "Asia/Tokyo", "Asia/Seoul", "Australia/Sydney"
        ]
        
        self.platforms = ["Win32", "MacIntel", "Linux x86_64"]
    
    def generate_profile(self, region: str = "global") -> BrowserProfile:
        """生成瀏覽器配置文件"""
        viewport = random.choice(self.viewports)
        
        # 根據地區調整配置
        if region == "middle_east":
            locale = "ar-AE"
            timezone = "Asia/Dubai"
        elif region == "asia":
            locale = random.choice(["zh-CN", "ja-JP", "ko-KR"])
            timezone = random.choice(["Asia/Shanghai", "Asia/Tokyo", "Asia/Seoul"])
        elif region == "us":
            locale = "en-US"
            timezone = random.choice(["America/New_York", "America/Los_Angeles"])
        else:
            locale = random.choice(self.locales)
            timezone = random.choice(self.timezones)
        
        return BrowserProfile(
            user_agent=self.ua_pool.get_random_agent(),
            viewport=viewport,
            locale=locale,
            timezone=timezone,
            platform=random.choice(self.platforms),
            screen={"width": viewport["width"], "height": viewport["height"]}
        )

class AntiDetectionScraper:
    """反檢測爬蟲核心類"""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        """初始化反檢測爬蟲"""
        self.proxy_manager = ProxyManager(proxy_list)
        self.profile_generator = BrowserProfileGenerator()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()
    
    async def start(self, profile: Optional[BrowserProfile] = None, region: str = "global"):
        """啟動瀏覽器"""
        if not profile:
            profile = self.profile_generator.generate_profile(region)
        
        self.playwright = await async_playwright().start()
        
        # 瀏覽器啟動參數
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--disable-crash-reporter",
            "--disable-oopr-debug-crash-dump",
            "--no-crash-upload",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-low-res-tiling",
            "--log-level=3",
            "--silent"
        ]
        
        # 代理設置
        proxy_config = None
        proxy = self.proxy_manager.get_next_proxy()
        if proxy:
            proxy_config = {"server": proxy}
        
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=launch_args,
            proxy=proxy_config
        )
        
        # 創建上下文
        self.context = await self.browser.new_context(
            user_agent=profile.user_agent,
            viewport=profile.viewport,
            locale=profile.locale,
            timezone_id=profile.timezone,
            screen=profile.screen,
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": f"{profile.locale},en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
        )
        
        # 注入反檢測腳本
        await self.context.add_init_script("""
            // 移除 webdriver 屬性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 偽造 Chrome 對象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 偽造權限查詢
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 偽造插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // 偽造語言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        self.page = await self.context.new_page()
        
        # 應用 stealth 模式
        await stealth(self.page)
        
        logger.info(f"瀏覽器已啟動，User-Agent: {profile.user_agent[:50]}...")
    
    async def navigate_with_retry(self, url: str, max_retries: int = 3) -> bool:
        """帶重試的導航"""
        for attempt in range(max_retries):
            try:
                # 隨機延遲
                await asyncio.sleep(random.uniform(1, 3))
                
                response = await self.page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                
                if response and response.status < 400:
                    logger.info(f"成功導航到 {url}")
                    return True
                else:
                    logger.warning(f"導航失敗，狀態碼: {response.status if response else 'None'}")
                    
            except Exception as e:
                logger.error(f"導航嘗試 {attempt + 1} 失敗: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
        
        return False
    
    async def human_like_scroll(self, duration: float = 2.0):
        """模擬人類滾動行為"""
        viewport_height = await self.page.evaluate("window.innerHeight")
        total_height = await self.page.evaluate("document.body.scrollHeight")
        
        if total_height <= viewport_height:
            return
        
        scroll_steps = random.randint(3, 8)
        step_delay = duration / scroll_steps
        
        for i in range(scroll_steps):
            scroll_y = (total_height / scroll_steps) * (i + 1)
            scroll_y += random.randint(-50, 50)  # 添加隨機性
            
            await self.page.evaluate(f"window.scrollTo(0, {scroll_y})")
            await asyncio.sleep(step_delay + random.uniform(0, 0.5))
    
    async def random_mouse_movement(self):
        """隨機鼠標移動"""
        viewport = self.page.viewport_size
        if viewport:
            x = random.randint(0, viewport["width"])
            y = random.randint(0, viewport["height"])
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def wait_with_random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """隨機延遲等待"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    def get_random_headers(self) -> dict:
        """獲取隨機請求頭"""
        ua_pool = UserAgentPool()
        return {
            "User-Agent": ua_pool.get_random_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    def get_browser_config(self, region: str = "global") -> dict:
        """獲取瀏覽器配置"""
        profile = self.profile_generator.generate_profile(region)
        return {
            "user_agent": profile.user_agent,
            "viewport": profile.viewport,
            "locale": profile.locale,
            "timezone": profile.timezone,
            "screen": profile.screen,
            "headers": self.get_random_headers()
        }
    
    async def close(self):
        """關閉瀏覽器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("瀏覽器已關閉")

class RetryStrategy:
    """重試策略"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """初始化重試策略"""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """獲取指數退避延遲"""
        delay = self.base_delay * (2 ** attempt)
        delay = min(delay, self.max_delay)
        # 添加隨機抖動
        jitter = random.uniform(0.1, 0.3) * delay
        return delay + jitter
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """執行帶重試的函數"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"嘗試 {attempt + 1} 失敗: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    delay = self.get_delay(attempt)
                    logger.info(f"等待 {delay:.2f} 秒後重試...")
                    await asyncio.sleep(delay)
        
        raise last_exception

# 工具函數
def create_scraper(proxy_list: Optional[List[str]] = None) -> AntiDetectionScraper:
    """創建反檢測爬蟲實例"""
    return AntiDetectionScraper(proxy_list)

async def test_anti_detection():
    """測試反檢測功能"""
    async with create_scraper() as scraper:
        # 測試基本功能
        success = await scraper.navigate_with_retry("https://httpbin.org/headers")
        if success:
            content = await scraper.page.content()
            logger.info("反檢測測試成功")
            return True
        else:
            logger.error("反檢測測試失敗")
            return False

if __name__ == "__main__":
    # 測試代碼
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_anti_detection())
