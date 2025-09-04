import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

export interface JobSearchRequest {
  query: string;
  location?: string;
  results_wanted?: number;
  use_ai_vision?: boolean;
}

export interface JobListing {
  title: string;
  company: string;
  location: string;
  salary?: string;
  description: string;
  job_url: string;
  site: string;
}

export interface JobSearchResponse {
  jobs: JobListing[];
  total_jobs: number;
  successful_sites: string[];
  confidence_score: number;
  ai_enhanced: boolean;
}

export const searchJobs = async (request: JobSearchRequest): Promise<JobSearchResponse> => {
  const response = await api.post('/jobs/search', request);
  return response.data;
};

export const getSupportedSites = async () => {
  const response = await api.get('/jobs/sites');
  return response.data;
};