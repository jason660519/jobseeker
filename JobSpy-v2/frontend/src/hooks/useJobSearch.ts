import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchJobs, getJobDetails } from '../services/jobService';
import { SearchRequest, JobSearchResponse } from '../types/job.types';

export const useJobSearch = () => {
  const queryClient = useQueryClient();

  const searchMutation = useMutation({
    mutationFn: searchJobs,
    onSuccess: (data) => {
      queryClient.setQueryData(['jobResults'], data);
    },
  });

  const { data: results, isLoading, error } = useQuery<JobSearchResponse>({
    queryKey: ['jobResults'],
    enabled: false,
  });

  return {
    searchJobs: searchMutation.mutate,
    results: results || null,
    isLoading: searchMutation.isPending || isLoading,
    error: searchMutation.error || error,
  };
};

export const useJobDetails = (jobId: string) => {
  return useQuery({
    queryKey: ['jobDetails', jobId],
    queryFn: () => getJobDetails(jobId),
    enabled: !!jobId,
  });
};