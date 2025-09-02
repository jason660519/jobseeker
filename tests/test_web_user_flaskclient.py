#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from types import SimpleNamespace

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def client():
    from web_app.app import app as flask_app
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def _make_stub_result(rows=2):
    df = pd.DataFrame([
        {
            'title': f'Test Job {i+1}',
            'company': 'ExampleCo',
            'location': 'Test City',
            'description': 'A great role',
            'salary_min': None,
            'salary_max': None,
            'salary_currency': '',
            'date_posted': '2025-01-01',
            'job_url': f'https://example.com/{i+1}',
            'job_url_direct': f'https://example.com/direct/{i+1}',
            'site': 'indeed',
            'job_type': 'fulltime',
            'is_remote': False,
        }
        for i in range(rows)
    ])
    return SimpleNamespace(
        total_jobs=len(df),
        successful_agents=[],
        failed_agents=[],
        total_execution_time=0.0,
        routing_decision=SimpleNamespace(confidence_score=0.9),
        combined_jobs_data=df,
    )


def test_homepage_renders(client):
    resp = client.get('/')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'id="searchForm"' in text or 'searchForm' in text


def test_search_flow_with_stubbed_backend(monkeypatch, client):
    # Patch backend search to avoid network and heavy deps
    import web_app.app as webapp
    monkeypatch.setattr(webapp, 'smart_scrape_jobs', lambda **kwargs: _make_stub_result(3))

    payload = {
        'query': 'python developer',
        'results_wanted': 5,
        'page': 1,
        'per_page': 5,
    }
    resp = client.post('/search', data=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['total_jobs'] == 3
    assert isinstance(data.get('jobs', []), list) and len(data['jobs']) == 3
    assert data.get('search_id')

    # Download JSON of the same search
    sid = data['search_id']
    dl = client.get(f'/download/{sid}/json')
    assert dl.status_code == 200
    assert dl.mimetype == 'application/json'


def test_search_validation_errors(client):
    # Missing query should 400 with error
    resp = client.post('/search', data={'query': ''})
    assert resp.status_code == 400
    j = resp.get_json()
    assert j and j.get('success') is False and 'error' in j

