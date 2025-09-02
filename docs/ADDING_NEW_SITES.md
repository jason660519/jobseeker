# Adding a New Job Site (Provider)

This guide explains how to add new providers (e.g. Taiwan 104/1111) to the jobseeker project in a stable, testable way.

## TL;DR

1. Add the site key to `jobseeker.model.Site` (e.g. `T104 = "104"`, `JOB_1111 = "1111"`).
2. Implement `Scraper` subclass under `jobseeker/<provider>/` returning a `JobResponse` of `JobPost` entries.
3. Register it in `jobseeker.__init__.py` `SCRAPER_MAPPING`.
4. (Optional) Add region hints to `jobseeker.intelligent_router` so the router can pick your provider for relevant queries.
5. Add a checkbox to the UI site selector (in `web_app/templates/base.html`) if you want it discoverable in the demo web app.
6. Add tests and data mapping verification.

## Contract

Implement a class that extends `jobseeker.model.Scraper`:

```python
from jobseeker.model import Scraper, ScraperInput, JobResponse

class MyProviderScraper(Scraper):
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        # Fetch data, then build JobPost objects and return JobResponse(jobs=[...])
        ...
```

Expected output types are defined in `jobseeker.model.JobPost` and related classes (e.g., `Compensation`).

## Field mapping tips

- Use `JobPost.description` and set `ScraperInput.description_format` (default markdown) accordingly.
- Fill `JobPost.compensation` when available: interval (hourly/daily/weekly/monthly/yearly), min/max, currency.
- Set `JobPost.location` via `Location(country, city, state)` if you have structured data; otherwise set string fields and we will display a formatted location.
- Set `JobPost.job_type` with the best matching enum(s) from `JobType`.

## Anti-bot and reliability

- Respect robots.txt and site Terms. Prefer public/official APIs.
- Use sensible headers and backoff. Consider the existing `anti_detection.py` utilities.
- Add timeouts, retries, and structured error messages.

## Intelligent routing integration

Update `jobseeker.intelligent_router.AgentType` and the relevant `GeographicRegion` if your provider is strong in a given region or industry. Then map the agent to a site key in `jobseeker.route_manager.RouteManager.AGENT_TO_SITE_MAPPING`.

## UI integration (optional)

If you want the demo web app to surface your provider:

- Add a checkbox to the site selector (see `web_app/templates/base.html`).
- Provide a description in `web_app/app.py:get_site_description`.

## Testing

Add unit tests under `tests/` that:

- Validate that your scraper returns a sensible `JobResponse`.
- Validate mapping to CSV via the export path.
- Use fixtures and mock HTTP where possible.

## Extending without touching core

For now, new providers still require adding a `Site` enum entry. We are iterating on a plugin mechanism to allow fully external providers to register without modifying the core enum. Until then, contributions should follow the above pattern.

## Example scaffolds

See `jobseeker/tw104/` and `jobseeker/tw1111/` for starter classes.

