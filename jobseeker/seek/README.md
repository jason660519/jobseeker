# Seek爬蟲引擎 🚀

一個智能化的Seek求職網站數據抓取與ETL處理引擎，集成了多種先進技術，提供高效、可靠的職位數據採集解決方案。

## ✨ 核心特色

### 🎯 多模式爬蟲架構
- **Traditional模式**: 基於Beautiful Soup的輕量級爬蟲
- **Enhanced模式**: 集成Playwright的動態內容處理
- **Hybrid模式**: 智能切換，兼顧效率與準確性

### 🔍 智能OCR處理
- 集成PaddleOCR，支持80+種語言
- 自動截圖與文字識別
- 智能內容提取與驗證

### 📊 完整ETL流程
- 數據清洗與標準化
- 薪資信息智能解析
- 工作類型自動識別
- 多格式數據導出

### ⚡ 高性能設計
- 異步並發處理
- 智能重試機制
- 內存優化管理
- 分佈式任務調度

## 🛠️ 技術架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Seek爬蟲引擎架構                          │
├─────────────────────────────────────────────────────────────┤
│  CLI接口層     │  命令行工具 │ 配置管理 │ 示例腳本          │
├─────────────────────────────────────────────────────────────┤
│  業務邏輯層    │  爬蟲引擎   │ ETL處理  │ 數據模型          │
├─────────────────────────────────────────────────────────────┤
│  技術組件層    │ Playwright  │ OCR引擎  │ 數據存儲          │
├─────────────────────────────────────────────────────────────┤
│  基礎設施層    │  異步框架   │ 日誌系統 │ 性能監控          │
└─────────────────────────────────────────────────────────────┘
```

## 📦 安裝指南

### 環境要求
- Python 3.8+
- Windows 10/11 或 Linux/macOS
- 至少 4GB RAM
- 2GB 可用磁盤空間

### 快速安裝

```bash
# 1. 安裝核心依賴
pip install -r requirements.txt

# 2. 安裝Playwright瀏覽器
playwright install

# 3. 安裝PaddleOCR（可選）
pip install paddlepaddle paddleocr
```

## 🚀 快速開始

### 命令行使用

```bash
# 搜索Python開發職位
python cli.py search "python developer" --location "Sydney" --pages 3

# 使用增強模式搜索
python cli.py search "data scientist" --mode enhanced --ocr

# 批量搜索多個關鍵詞
python cli.py search "software engineer" --location "Melbourne" --results 50
```

### Python API使用

```python
import asyncio
from seek_scraper_enhanced import SeekScraperEnhanced

async def main():
    # 創建爬蟲實例
    scraper = SeekScraperEnhanced(
        scraping_mode='hybrid',
        headless=True,
        enable_ocr=True
    )
    
    # 初始化
    await scraper.initialize()
    
    # 搜索職位
    jobs = await scraper.scrape_jobs(
        search_term="python developer",
        location="Sydney",
        max_pages=5
    )
    
    # 導出結果
    await scraper.export_results(jobs, 'json', 'results.json')
    
    # 清理資源
    await scraper.cleanup()

# 運行
asyncio.run(main())
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
