# Premium Data Services API

## Overview

Backend services providing premium job market data, salary insights, and company information to generate recurring revenue.

## Service Architecture

```
Premium Data API
├── Salary Intelligence Service
├── Company Insights Service  
├── Market Trends Analytics
├── Interview Preparation Data
└── Career Path Intelligence
```

## Technology Stack

- **Backend**: Python + FastAPI + Redis
- **Data Sources**: Multiple APIs + Web scraping
- **Database**: PostgreSQL + ClickHouse (analytics)
- **Caching**: Redis + CDN
- **Queue**: Celery + Redis

## Core Services

### 1. Salary Intelligence API

```python
# src/services/salary_service.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx
import asyncio
from typing import List, Optional
import redis

class SalaryRequest(BaseModel):
    job_title: str
    location: str
    experience_years: Optional[int] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None

class SalaryInsight(BaseModel):
    job_title: str
    location: str
    salary_range: dict
    market_percentiles: dict
    experience_breakdown: List[dict]
    trending_direction: str
    data_freshness: str
    sample_size: int

class SalaryService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.data_sources = {
            'glassdoor': 'https://api.glassdoor.com',
            'payscale': 'https://api.payscale.com',
            'salary_com': 'https://api.salary.com'
        }
    
    async def get_salary_insights(self, request: SalaryRequest) -> SalaryInsight:
        # Check cache first
        cache_key = f"salary:{request.job_title}:{request.location}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return SalaryInsight.parse_raw(cached_data)
        
        # Aggregate data from multiple sources
        salary_data = await self._aggregate_salary_data(request)
        
        # Process and analyze
        insights = self._process_salary_data(salary_data, request)
        
        # Cache for 24 hours
        self.redis_client.setex(
            cache_key, 
            86400, 
            insights.json()
        )
        
        return insights
    
    async def _aggregate_salary_data(self, request: SalaryRequest) -> dict:
        tasks = []
        
        # Glassdoor API
        tasks.append(self._fetch_glassdoor_data(request))
        
        # PayScale API  
        tasks.append(self._fetch_payscale_data(request))
        
        # Salary.com API
        tasks.append(self._fetch_salary_com_data(request))
        
        # LinkedIn Salary Insights (if available)
        tasks.append(self._fetch_linkedin_salary(request))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        return self._merge_salary_sources(valid_results)
    
    async def _fetch_glassdoor_data(self, request: SalaryRequest) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.data_sources['glassdoor']}/salaries",
                params={
                    'job_title': request.job_title,
                    'location': request.location,
                    'api_key': os.getenv('GLASSDOOR_API_KEY')
                }
            )
            return response.json()
    
    def _process_salary_data(self, aggregated_data: dict, request: SalaryRequest) -> SalaryInsight:
        # Calculate percentiles
        salaries = aggregated_data.get('salaries', [])
        
        if not salaries:
            raise HTTPException(status_code=404, detail="No salary data found")
        
        percentiles = self._calculate_percentiles(salaries)
        experience_breakdown = self._breakdown_by_experience(salaries)
        trending = self._calculate_trends(request.job_title, request.location)
        
        return SalaryInsight(
            job_title=request.job_title,
            location=request.location,
            salary_range={
                'min': min(salaries),
                'max': max(salaries),
                'median': percentiles['50th'],
                'average': sum(salaries) / len(salaries)
            },
            market_percentiles={
                '25th': percentiles['25th'],
                '50th': percentiles['50th'], 
                '75th': percentiles['75th'],
                '90th': percentiles['90th']
            },
            experience_breakdown=experience_breakdown,
            trending_direction=trending,
            data_freshness="Last updated 24 hours ago",
            sample_size=len(salaries)
        )

# FastAPI endpoints
app = FastAPI(title="JobSpy Premium Data API")
salary_service = SalaryService()

@app.post("/api/premium/salary-insights", response_model=SalaryInsight)
async def get_salary_insights(
    request: SalaryRequest,
    api_key: str = Depends(verify_api_key)
):
    return await salary_service.get_salary_insights(request)
```

### 2. Company Insights Service

```python
# src/services/company_service.py
class CompanyInsight(BaseModel):
    company_name: str
    industry: str
    size_range: str
    rating: float
    culture_scores: dict
    salary_competitiveness: str
    interview_difficulty: float
    work_life_balance: float
    career_growth: float
    benefits_rating: float
    hiring_trends: dict
    recent_news: List[dict]

class CompanyService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
    
    async def get_company_insights(self, company_name: str) -> CompanyInsight:
        cache_key = f"company:{company_name.lower()}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return CompanyInsight.parse_raw(cached_data)
        
        # Aggregate company data
        company_data = await self._fetch_company_data(company_name)
        
        insights = self._process_company_data(company_data, company_name)
        
        # Cache for 12 hours
        self.redis_client.setex(cache_key, 43200, insights.json())
        
        return insights
    
    async def _fetch_company_data(self, company_name: str) -> dict:
        tasks = [
            self._fetch_glassdoor_company(company_name),
            self._fetch_indeed_company(company_name),
            self._fetch_linkedin_company(company_name),
            self._fetch_crunchbase_data(company_name),
            self._fetch_news_sentiment(company_name)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._merge_company_sources([r for r in results if not isinstance(r, Exception)])
    
    def _process_company_data(self, data: dict, company_name: str) -> CompanyInsight:
        return CompanyInsight(
            company_name=company_name,
            industry=data.get('industry', 'Unknown'),
            size_range=data.get('size_range', 'Unknown'),
            rating=data.get('overall_rating', 0.0),
            culture_scores={
                'diversity': data.get('diversity_score', 0),
                'inclusion': data.get('inclusion_score', 0),
                'innovation': data.get('innovation_score', 0),
                'collaboration': data.get('collaboration_score', 0)
            },
            salary_competitiveness=data.get('salary_competitiveness', 'Average'),
            interview_difficulty=data.get('interview_difficulty', 0.0),
            work_life_balance=data.get('work_life_balance', 0.0),
            career_growth=data.get('career_growth', 0.0),
            benefits_rating=data.get('benefits_rating', 0.0),
            hiring_trends=data.get('hiring_trends', {}),
            recent_news=data.get('recent_news', [])
        )

@app.post("/api/premium/company-insights", response_model=CompanyInsight)
async def get_company_insights(
    company_name: str,
    api_key: str = Depends(verify_api_key)
):
    return await company_service.get_company_insights(company_name)
```

### 3. Market Trends Analytics

```python
# src/services/market_service.py
class MarketTrend(BaseModel):
    industry: str
    location: str
    trending_skills: List[dict]
    job_growth_rate: float
    salary_growth_rate: float
    demand_forecast: dict
    hot_companies: List[dict]
    emerging_roles: List[dict]
    skill_gap_analysis: dict

class MarketService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=2)
        self.clickhouse_client = clickhouse_connect.get_client()
    
    async def get_market_trends(self, industry: str, location: str) -> MarketTrend:
        # Query analytics database
        trends_data = await self._query_market_trends(industry, location)
        
        # Calculate growth rates
        growth_rates = self._calculate_growth_rates(industry, location)
        
        # Identify trending skills
        trending_skills = await self._identify_trending_skills(industry)
        
        # Forecast demand
        demand_forecast = self._forecast_job_demand(industry, location)
        
        return MarketTrend(
            industry=industry,
            location=location,
            trending_skills=trending_skills,
            job_growth_rate=growth_rates['job_growth'],
            salary_growth_rate=growth_rates['salary_growth'],
            demand_forecast=demand_forecast,
            hot_companies=await self._get_hot_companies(industry, location),
            emerging_roles=await self._get_emerging_roles(industry),
            skill_gap_analysis=await self._analyze_skill_gaps(industry)
        )

@app.get("/api/premium/market-trends", response_model=MarketTrend)
async def get_market_trends(
    industry: str,
    location: str,
    api_key: str = Depends(verify_api_key)
):
    return await market_service.get_market_trends(industry, location)
```

### 4. API Authentication & Rate Limiting

```python
# src/auth/api_auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import redis

security = HTTPBearer()
redis_client = redis.Redis(host='localhost', port=6379, db=3)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key = credentials.credentials
    
    # Check if API key exists and is valid
    user_data = redis_client.get(f"api_key:{api_key}")
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    user_info = json.loads(user_data)
    
    # Check subscription status
    if user_info['subscription_status'] != 'active':
        raise HTTPException(status_code=403, detail="Subscription expired")
    
    # Check rate limits
    rate_limit_key = f"rate_limit:{api_key}"
    current_requests = redis_client.get(rate_limit_key)
    
    if current_requests and int(current_requests) >= user_info['rate_limit']:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Increment request count
    redis_client.incr(rate_limit_key)
    redis_client.expire(rate_limit_key, 3600)  # 1 hour window
    
    return user_info

# Subscription tiers
SUBSCRIPTION_TIERS = {
    'basic': {
        'price': 9.99,
        'rate_limit': 1000,  # requests per hour
        'features': ['salary_insights', 'company_basic']
    },
    'professional': {
        'price': 19.99,
        'rate_limit': 5000,
        'features': ['salary_insights', 'company_insights', 'market_trends']
    },
    'enterprise': {
        'price': 49.99,
        'rate_limit': 20000,
        'features': ['all_features', 'priority_support', 'custom_analytics']
    }
}
```

### 5. Payment Integration

```python
# src/services/payment_service.py
import stripe
from datetime import datetime, timedelta

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class PaymentService:
    @staticmethod
    async def create_subscription(user_id: str, tier: str, payment_method_id: str):
        try:
            # Create Stripe customer
            customer = stripe.Customer.create(
                payment_method=payment_method_id,
                email=user_email,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    'price': SUBSCRIPTION_TIERS[tier]['stripe_price_id']
                }],
                expand=['latest_invoice.payment_intent']
            )
            
            # Generate API key
            api_key = generate_api_key()
            
            # Store in database
            await store_subscription(user_id, tier, api_key, subscription.id)
            
            return {
                'subscription_id': subscription.id,
                'api_key': api_key,
                'status': subscription.status
            }
            
        except stripe.error.CardError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/premium/subscribe")
async def create_subscription(
    user_id: str,
    tier: str,
    payment_method_id: str
):
    return await PaymentService.create_subscription(user_id, tier, payment_method_id)
```

## Deployment Configuration

### 6. Docker Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  premium-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/premiumdb
    depends_on:
      - redis
      - postgres
      - clickhouse
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=premiumdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  clickhouse:
    image: clickhouse/clickhouse-server
    ports:
      - "9000:9000"
```

### 7. API Usage Examples

```javascript
// JavaScript client usage
class JobSpyPremiumAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseURL = 'https://premium-api.jobspy.com';
    }

    async getSalaryInsights(jobTitle, location) {
        const response = await fetch(`${this.baseURL}/api/premium/salary-insights`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_title: jobTitle,
                location: location
            })
        });

        return await response.json();
    }

    async getCompanyInsights(companyName) {
        const response = await fetch(`${this.baseURL}/api/premium/company-insights`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: companyName
            })
        });

        return await response.json();
    }
}

// Usage in desktop app
const premiumAPI = new JobSpyPremiumAPI(userApiKey);

const salaryData = await premiumAPI.getSalaryInsights('Software Engineer', 'San Francisco');
const companyData = await premiumAPI.getCompanyInsights('Google');
```

## Revenue Model

### Monthly Subscription Tiers

| Tier | Price | Features | Rate Limit |
|------|-------|----------|------------|
| Basic | $9.99 | Salary insights, Basic company data | 1,000/hour |
| Pro | $19.99 | + Market trends, Interview prep | 5,000/hour |
| Enterprise | $49.99 | + Custom analytics, Priority support | 20,000/hour |

### Expected Revenue
- **Year 1**: 500 subscribers × $15 avg = $90,000
- **Year 2**: 2,000 subscribers × $20 avg = $480,000  
- **Year 3**: 5,000 subscribers × $25 avg = $1,500,000

This premium data service provides high-value, server-dependent features that cannot be pirated, creating sustainable recurring revenue while enhancing the core JobSpy experience.