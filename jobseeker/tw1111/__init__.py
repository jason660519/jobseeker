#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taiwan 1111 Job Bank scraper (scaffold)

This scaffold allows contributors to implement the 1111 scraper in a
structured way.
"""

from __future__ import annotations

from typing import Optional

from ..model import Scraper, ScraperInput, JobResponse


class Taiwan1111Scraper(Scraper):
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        # TODO: Implement 1111 scraping logic.
        return JobResponse(jobs=[])

