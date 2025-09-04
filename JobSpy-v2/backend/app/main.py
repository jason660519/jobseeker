from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import jobs, ai, users
from app.core.config import settings

app = FastAPI(
    title="JobSpy API v2",
    description="Modern AI-enhanced job search platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "JobSpy API v2 - Ready for AI-enhanced job searching!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)