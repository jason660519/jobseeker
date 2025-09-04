# JobSpy v2 - AI-Enhanced Job Search Platform

## Modern Architecture

This is the modernized version of JobSpy, featuring:

- FastAPI Backend: High-performance async API
- React + TypeScript Frontend: Modern, responsive UI  
- AI Vision Integration: OpenAI GPT-4V for intelligent scraping
- Microservices Architecture: Scalable and maintainable
- Docker Support: Easy development and deployment

## Project Structure

    JobSpy-v2/
    |-- backend/           # FastAPI backend application
    |-- frontend/          # React TypeScript frontend
    |-- shared/            # Shared types and utilities
    |-- docker/            # Docker configurations
    |-- scripts/           # Utility scripts
    |-- docs/              # Documentation

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API Key (for AI features)

### Quick Start

1. Clone and setup:
   git clone <repository>
   cd JobSpy-v2
   cp .env.example .env

2. Start with Docker:
   docker-compose up -d

3. Access applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Configuration

Create .env file with:

    DATABASE_URL=postgresql://jobspy:password@localhost:5432/jobspy
    REDIS_URL=redis://localhost:6379
    OPENAI_API_KEY=your_openai_api_key_here
    SECRET_KEY=your_secret_key_here

## Testing

    # Backend tests
    cd backend
    pytest
    
    # Frontend tests
    cd frontend
    npm test

## Key Features

- AI-Enhanced Scraping with GPT-4 Vision
- Real-time search results
- Progressive Web App support
- Responsive design
- Advanced filtering
- Async processing
- Redis caching
- Database indexing

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

MIT License - see LICENSE file

## Migration from v1

If migrating from original JobSpy:

1. Run migration script: python scripts/migration/migrate_legacy.py
2. Copy any custom configurations
3. Test functionality with new API endpoints
4. Update any integrations