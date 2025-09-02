#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight rules-based query parser to make the single-input UX LLM-ready.

It extracts a search term, optional location hints, remote flag, and any site hints
from a freeform user query (Chinese/English mixed supported heuristically).

This is intentionally simple so it can be replaced by an LLM parser later while
keeping the same interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import os
import json
import requests

from .model import Country


@dataclass
class ParsedQuery:
    search_term: str
    location: Optional[str] = None
    is_remote: bool = False
    site_hints: List[str] | None = None


REMOTE_TERMS = {
    "remote", "wfh", "work from home", "在家", "遠端", "遠程", "遠距", "远程", "远端"
}

# Basic site hints (both en/zh common variants)
SITE_HINTS = {
    "linkedin": "linkedin",
    "linkedIn": "linkedin",
    "領英": "linkedin",
    "领英": "linkedin",
    "indeed": "indeed",
    "glassdoor": "glassdoor",
    "ziprecruiter": "zip_recruiter",
    "zip recruiter": "zip_recruiter",
    "seek": "seek",
    "google": "google",
    "google jobs": "google",
}

# A small set of city hints (supplement Country enum)
CITY_HINTS = {
    # Taiwan
    "台北", "臺北", "新北", "台中", "臺中", "台南", "臺南", "高雄", "桃園", "新竹",
    # Hong Kong, Singapore, Japan
    "香港", "hong kong", "新加坡", "singapore", "東京", "tokyo", "大阪", "osaka",
}

# Common location synonyms mapping to Country enum's canonical key string (value[0])
LOC_SYNONYMS: Dict[str, str] = {
    # Australia
    "澳洲": "australia",
    "澳大利亞": "australia",
    "澳大利亚": "australia",
    # Taiwan
    "台灣": "taiwan",
    "臺灣": "taiwan",
    # Hong Kong / Singapore / Japan
    "香港": "hong kong",
    "新加坡": "singapore",
    "日本": "japan",
    # USA / UK / Canada / NZ
    "美國": "usa",
    "美国": "usa",
    "英國": "uk",
    "英国": "uk",
    "加拿大": "canada",
    "紐西蘭": "new zealand",
    "新西蘭": "new zealand",
}


def canonicalize_location(text: str) -> Optional[str]:
    """Return a canonical country string if a known synonym appears in text."""
    if not text:
        return None
    t = text.strip()
    lower = t.lower()
    # direct english match
    for c in Country:
        names = c.value[0].split(",")
        for name in names:
            name = name.strip()
            if name and name in lower:
                return name
    # chinese synonyms
    for k, v in LOC_SYNONYMS.items():
        if k in t or k in lower:
            return v
    return None


def _normalize_text(s: str) -> str:
    return s.strip()


def parse_user_query(query: str) -> ParsedQuery:
    if not query:
        return ParsedQuery(search_term="")

    original = query
    qnorm = _normalize_text(original)
    lower = qnorm.lower()

    # Remote detection
    is_remote = any(term in lower for term in REMOTE_TERMS)

    # Country-based location detection
    country_names: List[str] = []
    for c in Country:
        names = c.value[0].split(",")
        for name in names:
            name = name.strip()
            if not name:
                continue
            # Case-insensitive for latin, keep original for CJK comparing by containment
            if name in lower:
                country_names.append(name)

    # Add synonyms if present
    for k, v in LOC_SYNONYMS.items():
        if k in qnorm or k in lower:
            country_names.append(v)

    # City-based hints
    city_hits: List[str] = []
    for name in CITY_HINTS:
        if name in lower or name in qnorm:
            city_hits.append(name)

    # Site hints
    site_hits: List[str] = []
    for key, site in SITE_HINTS.items():
        if key in lower:
            site_hits.append(site)

    # Build a location string from first matches
    location = None
    # Prefer city over country if both present
    if city_hits:
        # Keep the first city occurrence
        location = city_hits[0]
    elif country_names:
        location = country_names[0]

    # Canonicalize location if possible
    cano = canonicalize_location(location or qnorm)
    if cano:
        location = cano

    # Build a cleaned search term: remove obvious markers
    cleaned = qnorm
    for term in REMOTE_TERMS:
        cleaned = cleaned.replace(term, "")
    for key in SITE_HINTS.keys():
        cleaned = cleaned.replace(key, "")
    # Remove city/country tokens (best-effort)
    for name in city_hits:
        cleaned = cleaned.replace(name, "")
    for name in set(country_names):
        cleaned = cleaned.replace(name, "")

    # Collapse whitespace
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        cleaned = qnorm  # fallback to original

    # Deduplicate site hints
    site_hints = list(dict.fromkeys(site_hits)) if site_hits else None

    return ParsedQuery(
        search_term=cleaned,
        location=location,
        is_remote=is_remote,
        site_hints=site_hints,
    )


def _truthy(val: Optional[str]) -> bool:
    if val is None:
        return False
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_user_query_llm(query: str) -> Optional[ParsedQuery]:
    """
    Optional LLM-backed parsing. Controlled by env vars:
      ENABLE_LLM_PARSER=true|false
      LLM_PROVIDER=openai (default)
      OPENAI_API_KEY=<token>
      OPENAI_BASE_URL=https://api.openai.com/v1 (optional)
      LLM_MODEL=gpt-4o-mini (default)
    Returns None if not enabled or on any failure.
    """
    if not _truthy(os.getenv("ENABLE_LLM_PARSER")):
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider != "openai":
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    sys_msg = (
        "You are a precise intent parser for a job search app. "
        "Given a single freeform user query (may include language mixing), "
        "extract a strict JSON object with keys: search_term (string), "
        "location (string or null), is_remote (boolean), site_hints (array of strings from: "
        "['linkedin','indeed','glassdoor','zip_recruiter','seek','google']). "
        "Do not include any other keys and do not add trailing text."
    )
    user_msg = f"Query: {query}"

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg},
                ],
                # Encourage JSON-only output
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        obj: Dict[str, Any] = json.loads(content)

        search_term = str(obj.get("search_term") or "").strip()
        if not search_term:
            return None
        location = obj.get("location")
        if location is not None:
            location = str(location).strip() or None
            # canonicalize LLM-provided location
            cano = canonicalize_location(location)
            if cano:
                location = cano
        is_remote = bool(obj.get("is_remote", False))
        site_hints_raw = obj.get("site_hints") or []
        site_hints: List[str] = []
        for s in site_hints_raw:
            s_norm = str(s).strip().lower()
            # Map to canonical names
            if s_norm in SITE_HINTS:
                site_hints.append(SITE_HINTS[s_norm])
            else:
                # Already canonical?
                if s_norm in {"linkedin","indeed","glassdoor","zip_recruiter","seek","google"}:
                    site_hints.append(s_norm)

        # Deduplicate
        site_hints = list(dict.fromkeys(site_hints)) if site_hints else None

        return ParsedQuery(
            search_term=search_term,
            location=location,
            is_remote=is_remote,
            site_hints=site_hints,
        )
    except Exception:
        return None


def parse_user_query_smart(query: str) -> ParsedQuery:
    """Try LLM parsing if enabled; otherwise fallback to rules."""
    llm_parsed = parse_user_query_llm(query)
    if llm_parsed is not None:
        return llm_parsed
    return parse_user_query(query)
