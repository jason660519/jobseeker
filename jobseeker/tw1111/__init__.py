#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taiwan 1111 Job Bank scraper (scaffold)

This scaffold allows contributors to implement the 1111 scraper in a
structured way.
"""

from __future__ import annotations

from typing import Optional, List

from ..model import (
    Scraper,
    ScraperInput,
    JobResponse,
    JobPost,
    Location,
    Country,
    Site,
)
from ..util import create_session, create_logger, extract_emails_from_text
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlencode
from datetime import datetime


class Taiwan1111Scraper(Scraper):
    base_url = "https://www.1111.com.tw"
    search_path = "/search/job"

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None
    ):
        super().__init__(site=Site.JOB_1111, proxies=proxies, ca_cert=ca_cert, user_agent=user_agent)
        self.site = Site.JOB_1111
        self.logger = create_logger("1111")
        # 使用 requests 會話（帶重試），以降低被阻擋風險
        # 使用 requests 會話（具重試）。若後續需要更強抗封鎖，可切換 is_tls=True 並改用 execute_request 調用。
        self.session = create_session(
            proxies=self.proxies, ca_cert=self.ca_cert, is_tls=False, has_retry=True, delay=1, clear_cookies=True
        )
        self.headers = {
            "User-Agent": user_agent
            or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            ),
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        self._seen_urls: set[str] = set()

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        self.logger.info("Start scraping 1111 search results")
        results_wanted = scraper_input.results_wanted or 15
        offset = scraper_input.offset or 0
        search_term = (scraper_input.search_term or "").strip()

        jobs: List[JobPost] = []
        page = 1
        # 使用固定排序（ab/desc：以最近發布排序）
        col, sort = "ab", "desc"

        # 迭代分頁直到收集足夠結果或無更多
        while len(self._seen_urls) < results_wanted + offset:
            params = {"page": page, "col": col, "sort": sort}
            if search_term:
                params["ks"] = search_term

            url = urljoin(self.base_url, self.search_path)
            try:
                resp = self.session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=min(20, scraper_input.request_timeout or 20),
                )
            except Exception as e:
                self.logger.error(f"1111: request error on page {page}: {e}")
                break

            if not getattr(resp, "ok", False):
                self.logger.info(f"1111 responded with status {getattr(resp, 'status_code', '?')} on page {page}")
                break

            html = resp.text or ""
            page_jobs = self._parse_search_page(html)
            # 僅在找不到任何職缺且確實呈現錯誤頁 DOM 時才停止
            if not page_jobs and self._is_blocked_dom(html):
                self.logger.warning("1111 likely returned anti-bot/error page; stopping")
                break
            if not page_jobs:
                self.logger.info(f"1111 found no jobs on page {page}")
                break

            # 去重並累加
            new_count = 0
            for job in page_jobs:
                if job.job_url in self._seen_urls:
                    continue
                self._seen_urls.add(job.job_url)
                jobs.append(job)
                new_count += 1
                if len(self._seen_urls) >= results_wanted + offset:
                    break

            self.logger.info(f"1111 collected {new_count} new jobs on page {page}")
            page += 1

        # 應用 offset 與 results_wanted 限制
        jobs = jobs[offset : offset + results_wanted]
        return JobResponse(jobs=jobs)

    def _parse_search_page(self, html: str) -> List[JobPost]:
        """從搜尋頁面解析職缺（優先使用 LD+JSON 結構化資料）。"""
        soup = BeautifulSoup(html, "html.parser")
        jobs: List[JobPost] = []

        # 1) 嘗試解析 application/ld+json 中的 CollectionPage -> ItemList
        try:
            scripts = soup.find_all("script", {"type": "application/ld+json"})
            for s in scripts:
                if not s.string:
                    continue
                data = json.loads(s.string)
                # 可能是 list 或單物件
                candidates = data if isinstance(data, list) else [data]
                for obj in candidates:
                    if not isinstance(obj, dict):
                        continue
                    if obj.get("@type") == "CollectionPage" and obj.get("mainEntity", {}).get("@type") in ("ItemList",):
                        elements = obj.get("mainEntity", {}).get("itemListElement", [])
                        for el in elements:
                            item = (el or {}).get("item", {})
                            job_post = self._build_job_from_ld(item)
                            if job_post:
                                jobs.append(job_post)
        except Exception as e:
            self.logger.debug(f"1111 ld+json parse error: {e}")

        # 2) 後備：直接從連結抽取（a[href^='/job/']）
        if not jobs:
            anchors = soup.select("a[href^='/job/']")
            for a in anchors:
                href = a.get("href")
                title = a.get_text(strip=True)
                if not href or not title or not href.startswith("/job/"):
                    continue
                job_url = urljoin(self.base_url, href)
                job_id = f"tw1111-{href.strip('/').split('/')[-1]}"
                jobs.append(
                    JobPost(
                        id=job_id,
                        title=title,
                        company_name=None,
                        location=Location(country=Country.TAIWAN),
                        job_url=job_url,
                    )
                )

        return jobs

    def _build_job_from_ld(self, item: dict) -> JobPost | None:
        try:
            title = item.get("title")
            url = item.get("url")
            if not title or not url:
                return None
            job_url = url if url.startswith("http") else urljoin(self.base_url, url)

            company_name = None
            org = item.get("hiringOrganization") or {}
            if isinstance(org, dict):
                company_name = org.get("name")

            loc_name = None
            loc = item.get("jobLocation") or {}
            if isinstance(loc, dict):
                loc_name = loc.get("name")

            # 嘗試解析日期（多數為 yyyy/mm/dd）
            date_posted = None
            dp = item.get("datePosted")
            if isinstance(dp, str):
                try:
                    # 接受 2025/8/27 或 2025-08-27
                    dp_norm = dp.replace(".", "/").replace("-", "/")
                    dt = datetime.strptime(dp_norm, "%Y/%m/%d").date()
                    date_posted = dt
                except Exception:
                    try:
                        date_posted = datetime.fromisoformat(dp[:10]).date()
                    except Exception:
                        date_posted = None

            description = item.get("description")
            emails = extract_emails_from_text(description) if description else None

            job_id = f"tw1111-{job_url.rstrip('/').split('/')[-1]}"

            return JobPost(
                id=job_id,
                title=title,
                company_name=company_name,
                location=Location(city=loc_name, country=Country.TAIWAN),
                job_url=job_url,
                description=description,
                date_posted=date_posted,
                emails=emails,
            )
        except Exception:
            return None

    def _is_blocked_dom(self, html: str) -> bool:
        try:
            soup = BeautifulSoup(html, "html.parser")
            if soup.select(".error-page, .error-card"):
                # 如同測試端邏輯，僅在確實存在錯誤頁容器時才視為阻擋
                return True
        except Exception:
            pass
        return False

