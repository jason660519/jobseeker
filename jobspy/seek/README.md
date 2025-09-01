# Seek.com.au Job Scraper

A comprehensive Python scraper for extracting job postings from Seek.com.au, Australia's leading job board.

## Features

- 🔍 **Advanced Search**: Search by keywords, location, job type, and remote work options
- 📊 **Structured Data**: Extract detailed job information including salary, company, location
- 🚀 **Fast & Reliable**: Built-in retry mechanisms and rate limiting
- 📁 **Multiple Formats**: Export results to CSV or JSON
- 🛡️ **Proxy Support**: Use proxies to avoid rate limiting
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Installation

This scraper is part of the jobseeker package. Make sure you have the required dependencies:

```bash
pip install requests beautifulsoup4 lxml
```

## Quick Start

### Command Line Usage

```bash
# Basic search
python main.py --search "python developer" --location "Sydney"

# Advanced search with filters
python main.py --search "data scientist" --location "Melbourne" --job-type "full-time" --max-results 100

# Remote work search
python main.py --search "software engineer" --remote --output remote_jobs.json

# Part-time jobs in Brisbane
python main.py --search "marketing" --location "Brisbane" --job-type "part-time"
```

### Python API Usage

```python
from seek import SeekScraper
from jobseeker.model import JobType

# Initialize scraper
scraper = SeekScraper()

# Search for jobs
jobs = scraper.scrape_jobs(
    search_term="python developer",
    location="Sydney",
    max_results=50,
    job_type=JobType.FULL_TIME,
    is_remote=False
)

# Process results
for job in jobs:
    print(f"{job.title} at {job.company}")
    print(f"Location: {job.location.city}, {job.location.state}")
    print(f"URL: {job.job_url}")
    print("-" * 50)
```

## Command Line Options

### Required Arguments
- `--search, -s`: Job search keywords (e.g., 'python developer', 'marketing manager')

### Optional Arguments
- `--location, -l`: Location to search in (e.g., 'Sydney', 'Melbourne', 'Brisbane')
- `--max-results, -m`: Maximum number of job results to retrieve (default: 50)
- `--job-type, -t`: Filter by job type (full-time, part-time, contract, temporary, internship)
- `--remote, -r`: Search for remote work opportunities
- `--output, -o`: Output file path (extension determines format: .csv or .json)
- `--format, -f`: Output format (csv, json) - default: csv
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--timeout`: Request timeout in seconds (default: 30)
- `--proxy`: Proxy URL (e.g., 'http://proxy.example.com:8080')
- `--user-agent`: Custom User-Agent string
- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress all output except errors

## Examples

### 1. Basic Job Search
```bash
python main.py --search "software engineer" --location "Sydney"
```

### 2. Large Scale Scraping
```bash
python main.py --search "data analyst" --max-results 200 --output data_jobs.csv
```

### 3. Remote Work Focus
```bash
python main.py --search "digital marketing" --remote --format json
```

### 4. Contract Positions
```bash
python main.py --search "project manager" --job-type contract --location "Melbourne"
```

### 5. Using Proxy
```bash
python main.py --search "developer" --proxy "http://proxy.example.com:8080"
```

## Output Formats

### CSV Output
The CSV format includes the following columns:
- `title`: Job title
- `company`: Company name
- `city`: Job location city
- `state`: Job location state
- `country`: Job location country
- `job_type`: Type of employment
- `description`: Job description snippet
- `job_url`: Direct link to job posting
- `min_salary`: Minimum salary (if available)
- `max_salary`: Maximum salary (if available)
- `salary_interval`: Salary interval (hourly, yearly, etc.)
- `currency`: Salary currency
- `date_posted`: Date job was posted
- `scraped_at`: Timestamp when data was scraped

### JSON Output
The JSON format provides a structured representation with nested objects for location and salary information.

## Job Types

Supported job types for filtering:
- `full-time`: Full-time positions
- `part-time`: Part-time positions
- `contract`: Contract/freelance work
- `temporary`: Temporary positions
- `internship`: Internship opportunities

## Rate Limiting & Best Practices

- **Default Delay**: 1 second between requests
- **Timeout**: 30 seconds per request
- **Retry Logic**: Automatic retries for failed requests
- **Respectful Scraping**: Built-in delays to avoid overwhelming the server

### Recommended Settings
```bash
# For large scraping jobs
python main.py --search "your_term" --delay 2.0 --timeout 60 --max-results 500

# For quick searches
python main.py --search "your_term" --delay 0.5 --max-results 20
```

## Error Handling

The scraper includes comprehensive error handling:
- Network timeouts and connection errors
- Rate limiting responses
- Invalid HTML parsing
- Missing job elements

All errors are logged with detailed information for debugging.

## Integration with jobseeker

This Seek scraper is designed to integrate seamlessly with the jobseeker framework:

```python
from jobseeker import scrape_jobs

# Use Seek through jobseeker
jobs_df = scrape_jobs(
    site_name="seek",  # When SEEK is added to jobseeker
    search_term="python developer",
    location="Sydney",
    results_wanted=50
)
```

## Troubleshooting

### Common Issues

1. **No jobs found**
   - Check your search terms and location
   - Try broader search criteria
   - Verify internet connection

2. **Rate limiting**
   - Increase delay between requests: `--delay 2.0`
   - Use proxy: `--proxy http://your-proxy.com:8080`
   - Reduce max results per session

3. **Timeout errors**
   - Increase timeout: `--timeout 60`
   - Check network connection
   - Try using a proxy

### Debug Mode
```bash
python main.py --search "your_term" --verbose
```

## Legal Considerations

- This scraper is for educational and research purposes
- Respect Seek.com.au's robots.txt and terms of service
- Use reasonable delays between requests
- Don't overwhelm the server with too many concurrent requests
- Consider using official APIs when available

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is part of the jobseeker package. Please refer to the main project license.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Note**: This scraper is designed to work with Seek.com.au's current website structure. Website changes may require updates to the scraping logic.
