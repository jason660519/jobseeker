#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1111 人力銀行（tw1111）隨機用戶行為測試

本測試模擬真實使用者在 1111 搜尋與瀏覽職缺的行為，
包含：隨機關鍵字、隨機使用者代理、隨機頁碼與滾動/點擊操作。

說明：
- 優先使用 Playwright 進行端對端互動測試；若 Playwright 或瀏覽器未安裝，
  則跳過該測試。
- 提供 requests 輕量檢查以驗證基本可達性與列表抓取能力，若偵測到反爬/風控頁面，
  將安全地跳過以避免誤報。

標記：
- integration, network：屬於整合與網路測試
- slow：可能較慢（需實際載入頁面與互動）
"""

from __future__ import annotations

import os
import random
import re
import time
from typing import List

import pytest
import requests


BASE_SEARCH_URL = "https://www.1111.com.tw/search/job"


def _random_user_agent() -> str:
    agents: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-G996B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Mobile Safari/537.36",
    ]
    return random.choice(agents)


def _build_random_query_url() -> str:
    # 中英混合關鍵字池（偏向常見職稱/技能以提高命中率）
    keywords = [
        "python", "java", "工程師", "資料", "數據", "設計", "行銷", "財務",
        "行政", "客服", "測試", "DevOps", "前端", "後端",
    ]
    ks = random.choice(keywords)

    # 依 1111 目前行為常用參數：
    # - page: 頁碼（1 開始）
    # - col/sort: 排序欄位與方向（例如 ab/desc 代表依發布時間較新優先）
    page = random.randint(1, 2)
    col = random.choice(["ab", "da"])  # 發布時間 / 相關度（實際依站方為準）
    sort = random.choice(["desc", "asc"])  # 新到舊 / 舊到新

    # location 與其他參數若需可擴充；先聚焦於最穩定的 ks 搜尋
    return f"{BASE_SEARCH_URL}?page={page}&col={col}&sort={sort}&ks={ks}"


def _looks_like_blocked(html_text: str) -> bool:
    """更精準的風控頁偵測：僅在實際 DOM 標籤 class 中出現時才視為阻擋。

    注意：頁面全域樣式中可能包含 .error-page/.error-card 的 CSS 定義，
    不能僅以子字串判斷，以免誤判。
    """
    # 僅匹配出現在 HTML 標籤的 class 屬性中，而非 style 區塊
    pattern = r'class\s*=\s*"[^"]*(?:error-page|error-card)[^"]*"'
    return bool(re.search(pattern, html_text, flags=re.IGNORECASE))


@pytest.mark.integration
@pytest.mark.network
def test_tw1111_random_search_lightweight_requests():
    """使用 requests 輕量檢查：隨機 UA 與關鍵字抓取列表連結。"""
    url = _build_random_query_url()
    headers = {"User-Agent": _random_user_agent()}

    resp = requests.get(url, headers=headers, timeout=20)
    assert resp.status_code in (200, 304), f"Unexpected status: {resp.status_code}"

    text = resp.text
    # 從搜尋頁面提取職缺連結（/job/數字）；若有連結則視為可用
    links = re.findall(r'href=\"(/job/\d+)\"', text)
    if not links and _looks_like_blocked(text):
        pytest.skip("tw1111 appears to present an anti-bot/error page; skipping.")
    # 若無連結，容忍一次隨機 miss（站方 UI / A/B 測試）；以 skip 代替失敗
    if not links:
        pytest.skip("No job links found on search page; possibly UI variant or blocked.")

    # 抽一條進一步檢查細節頁是否可達
    job_path = random.choice(links)
    job_url = f"https://www.1111.com.tw{job_path}"
    time.sleep(random.uniform(0.5, 1.2))  # 禮貌性延遲
    detail = requests.get(job_url, headers=headers, timeout=20)
    assert detail.status_code in (200, 304)
    # 細節頁若含有錯誤 DOM 標籤且無內容時才判定阻擋
    if _looks_like_blocked(detail.text):
        # 若仍可見到基本 1111 文案或標題，視為可用
        if ("1111人力銀行" not in detail.text) and ("工作內容" not in detail.text) and ("職務" not in detail.text):
            pytest.skip("Detail page looks blocked; skipping.")

    # 簡單檢查標題包含站名，確保為職缺頁
    assert ("1111人力銀行" in detail.text) or ("1111" in detail.text)


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.slow
def test_tw1111_random_user_flow_playwright():
    """
    使用 Playwright 模擬隨機用戶流程：
    1) 隨機關鍵字與參數打開搜尋頁
    2) 滾動與等待
    3) 隨機點擊一筆職缺
    4) 驗證職缺頁面載入成功（以標題/關鍵字為準）
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not installed. Skipping browser-based test.")

    # 可使用環境變數覆蓋是否 headless
    headless = os.environ.get("PW_HEADLESS", "1") != "0"

    url = _build_random_query_url()
    user_agent = _random_user_agent()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless, args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ])
        except Exception as e:
            pytest.skip(f"Playwright runtime not ready (browsers not installed): {e}")
        context = browser.new_context(
            user_agent=user_agent,
            viewport={
                "width": random.randint(360, 1600),
                "height": random.randint(640, 1200),
            },
            locale="zh-TW",
        )
        page = context.new_page()
        try:
            page.set_default_timeout(15000)
            page.set_extra_http_headers({
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            })

            page.goto(url, wait_until="domcontentloaded")
            # 簡單滾動幾次模擬用戶瀏覽
            for _ in range(random.randint(1, 3)):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.6)")
                time.sleep(random.uniform(0.4, 1.0))

            html = page.content()
            if _looks_like_blocked(html):
                pytest.skip("tw1111 shows anti-bot/error page in Playwright; skipping.")

            # 找到職缺卡片連結（a[href^="/job/"]）
            job_links = page.locator('a[href^="/job/"]')
            count = job_links.count()

            # 若找不到，嘗試等待動態載入
            if count == 0:
                page.wait_for_timeout(1500)
                count = job_links.count()

            if count == 0:
                pytest.skip("No job links found via Playwright; possibly dynamic/UI change.")

            idx = random.randint(0, min(count - 1, 5))  # 避免過深，最多挑前 6 筆
            with page.expect_navigation(wait_until="domcontentloaded"):
                job_links.nth(idx).click(force=True)

            # 確認進入職缺頁：標題包含 1111，或頁面含有典型中文關鍵字
            title = page.title()
            body_text = page.inner_text("body")[:5000]
            assert ("1111" in title) or ("1111人力銀行" in body_text) or ("工作內容" in body_text) or ("職務" in body_text)

        finally:
            context.close()
            browser.close()
