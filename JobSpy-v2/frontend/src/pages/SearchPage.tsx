import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { searchJobs } from '../services/api';

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [useAI, setUseAI] = useState(true);
  
  const searchMutation = useMutation({
    mutationFn: searchJobs,
    onSuccess: (data) => {
      console.log('Search results:', data);
    },
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    searchMutation.mutate({
      query,
      location,
      results_wanted: 20,
      use_ai_vision: useAI
    });
  };
  
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white p-8 rounded-lg shadow-lg">
        <h2 className="text-xl font-semibold mb-6">Search for Jobs</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Title or Keywords
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g. Software Engineer, Data Scientist"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location (Optional)
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g. New York, London, Remote"
            />
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="useAI"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="useAI" className="text-sm text-gray-700">
              Enable AI-Enhanced Scraping (Beta)
            </label>
          </div>
          
          <button
            type="submit"
            disabled={searchMutation.isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {searchMutation.isLoading ? 'Searching...' : 'Search Jobs'}
          </button>
        </form>
        
        {searchMutation.error && (
          <div className="mt-4 p-4 bg-red-50 rounded-md">
            <p className="text-red-800">
              Error: {(searchMutation.error as Error).message}
            </p>
          </div>
        )}
        
        {searchMutation.data && (
          <div className="mt-6">
            <h3 className="font-semibold mb-2">Search Results</h3>
            <p>Found {searchMutation.data.total_jobs} jobs</p>
            {/* TODO: Display job results */}
          </div>
        )}
      </div>
    </div>
  );
};