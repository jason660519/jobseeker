from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.services.job_search import JobSearchService
from app.models.job import JobSearchRequest, JobSearchResponse

router = APIRouter()

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    request: JobSearchRequest,
    job_service: JobSearchService = Depends()
):
    """Enhanced job search with AI vision capabilities"""
    try:
        result = await job_service.search_with_ai_enhancement(
            query=request.query,
            location=request.location,
            results_wanted=request.results_wanted,
            use_ai_vision=request.use_ai_vision
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sites")
async def get_supported_sites():
    """Get list of supported job sites"""
    return {
        "sites": [
            {"name": "indeed", "region": "global", "ai_enhanced": True},
            {"name": "linkedin", "region": "global", "ai_enhanced": True},
            {"name": "glassdoor", "region": "global", "ai_enhanced": True},
        ]
    }