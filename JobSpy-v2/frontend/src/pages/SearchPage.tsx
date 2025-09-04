import React, { useState } from 'react';
import { SearchBar } from '../components/SearchBar';
import { JobResults } from '../components/JobResults';
import { Filters } from '../components/Filters';
import { useJobSearch } from '../hooks/useJobSearch';
import { SearchFilters } from '../types/job.types';

export const SearchPage: React.FC = () => {
  const [filters, setFilters] = useState<SearchFilters>({
    location: '',
    jobType: '',
    experienceLevel: '',
    salaryRange: { min: 0, max: 0 },
    useAI: true
  });

  const { searchJobs, results, isLoading, error } = useJobSearch();

  const handleSearch = async (query: string) => {
    await searchJobs({ query, ...filters });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Find Your Next Opportunity
          </h1>
          <p className="text-lg text-gray-600">
            AI-powered job search across multiple platforms
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1">
            <Filters filters={filters} onFiltersChange={setFilters} />
          </div>
          
          <div className="lg:col-span-3">
            <div className="mb-6">
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            </div>
            
            <JobResults 
              results={results} 
              isLoading={isLoading} 
              error={error} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};
