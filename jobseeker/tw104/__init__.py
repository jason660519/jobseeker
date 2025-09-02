#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taiwan 104 Job Bank scraper (scaffold)

This is a scaffold Scraper implementation intended for contributors to
fill in. It conforms to the Scraper interface and should return a
JobResponse with a list of JobPost entries.

Implementation notes:
- Prefer official APIs if available; otherwise, be mindful of robots.txt
  and anti-bot policies. Use respectful delays and headers.
- Map fields to jobseeker.model.JobPost and Compensation consistently.
- Use markdown for description by default.
"""

from __future__ import annotations

from typing import Optional

from ..model import Scraper, ScraperInput, JobResponse


class Taiwan104Scraper(Scraper):
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        # TODO: Implement 104 scraping logic.
        # For now, return empty result to keep integration stable.
        return JobResponse(jobs=[])

