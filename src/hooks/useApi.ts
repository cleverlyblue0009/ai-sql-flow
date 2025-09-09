import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { dashboardApi, dataQualityApi, migrationApi, authApi, checkApiHealth } from '@/lib/api';

// Query Keys
export const QUERY_KEYS = {
  dashboard: {
    overview: ['dashboard', 'overview'] as const,
    metrics: ['dashboard', 'metrics'] as const,
    activities: (limit?: number) => ['dashboard', 'activities', limit] as const,
    quickStats: ['dashboard', 'quick-stats'] as const,
    systemStatus: ['dashboard', 'system-status'] as const,
    performanceTrends: (days?: number) => ['dashboard', 'performance-trends', days] as const,
    costAnalysis: ['dashboard', 'cost-analysis'] as const,
  },
  dataQuality: {
    recentUploads: (limit?: number) => ['data-quality', 'uploads', limit] as const,
    analysis: (fileId: string) => ['data-quality', 'analysis', fileId] as const,
    cleaningResults: (jobId: string) => ['data-quality', 'results', jobId] as const,
  },
  migration: {
    active: ['migration', 'active'] as const,
    history: (limit?: number) => ['migration', 'history', limit] as const,
    status: (migrationId: string) => ['migration', 'status', migrationId] as const,
  },
  auth: {
    currentUser: ['auth', 'current-user'] as const,
  },
  health: ['api', 'health'] as const,
} as const;

// Dashboard Hooks
export const useDashboardOverview = () => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.overview,
    queryFn: async () => {
      const response = await dashboardApi.getOverview();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
};

export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.metrics,
    queryFn: async () => {
      const response = await dashboardApi.getMetrics();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
};

export const useRecentActivities = (limit: number = 20) => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.activities(limit),
    queryFn: async () => {
      const response = await dashboardApi.getActivities(limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 15000, // 15 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useQuickStats = () => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.quickStats,
    queryFn: async () => {
      const response = await dashboardApi.getQuickStats();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
};

export const useSystemStatus = () => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.systemStatus,
    queryFn: async () => {
      const response = await dashboardApi.getSystemStatus();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 15000,
    refetchInterval: 30000,
  });
};

export const usePerformanceTrends = (days: number = 30) => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.performanceTrends(days),
    queryFn: async () => {
      const response = await dashboardApi.getPerformanceTrends(days);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
};

export const useCostAnalysis = () => {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard.costAnalysis,
    queryFn: async () => {
      const response = await dashboardApi.getCostAnalysis();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
};

// Data Quality Hooks
export const useRecentUploads = (limit: number = 10) => {
  return useQuery({
    queryKey: QUERY_KEYS.dataQuality.recentUploads(limit),
    queryFn: async () => {
      const response = await dataQualityApi.getRecentUploads(limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
};

export const useFileAnalysis = (fileId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: QUERY_KEYS.dataQuality.analysis(fileId),
    queryFn: async () => {
      const response = await dataQualityApi.getAnalysis(fileId);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled: enabled && !!fileId,
    staleTime: 300000, // 5 minutes
  });
};

export const useCleaningResults = (jobId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: QUERY_KEYS.dataQuality.cleaningResults(jobId),
    queryFn: async () => {
      const response = await dataQualityApi.getCleaningResults(jobId);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled: enabled && !!jobId,
    refetchInterval: (data) => {
      // Stop refetching if the job is complete
      return data?.status === 'completed' ? false : 5000;
    },
  });
};

// Migration Hooks
export const useActiveMigrations = () => {
  return useQuery({
    queryKey: QUERY_KEYS.migration.active,
    queryFn: async () => {
      const response = await migrationApi.getActiveMigrations();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
};

export const useMigrationHistory = (limit: number = 20) => {
  return useQuery({
    queryKey: QUERY_KEYS.migration.history(limit),
    queryFn: async () => {
      const response = await migrationApi.getMigrationHistory(limit);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
};

export const useMigrationStatus = (migrationId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: QUERY_KEYS.migration.status(migrationId),
    queryFn: async () => {
      const response = await migrationApi.getMigrationStatus(migrationId);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    enabled: enabled && !!migrationId,
    refetchInterval: (data) => {
      // Stop refetching if the migration is complete
      return data?.status === 'completed' ? false : 5000;
    },
  });
};

// Authentication Hooks
export const useCurrentUser = () => {
  return useQuery({
    queryKey: QUERY_KEYS.auth.currentUser,
    queryFn: async () => {
      const response = await authApi.getCurrentUser();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 300000, // 5 minutes
    retry: false, // Don't retry auth failures
  });
};

// API Health Hook
export const useApiHealth = () => {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: checkApiHealth,
    staleTime: 60000, // 1 minute
    refetchInterval: 120000, // Check every 2 minutes
    retry: 3,
  });
};

// Mutation Hooks
export const useFileUpload = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: any }) =>
      dataQualityApi.uploadFile(file, options),
    onSuccess: (data) => {
      // Invalidate and refetch recent uploads
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dataQuality.recentUploads() });
      
      if (!data.error) {
        toast.success('File uploaded successfully!');
      } else {
        toast.error(data.error);
      }
    },
    onError: (error: Error) => {
      toast.error(`Upload failed: ${error.message}`);
    },
  });
};

export const useStartCleaning = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ fileId, config }: { fileId: string; config: any }) =>
      dataQualityApi.startCleaning(fileId, config),
    onSuccess: (data) => {
      if (!data.error) {
        toast.success('Cleaning process started!');
        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard.activities() });
      } else {
        toast.error(data.error);
      }
    },
    onError: (error: Error) => {
      toast.error(`Failed to start cleaning: ${error.message}`);
    },
  });
};

export const useStartMigration = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (config: any) => migrationApi.startMigration(config),
    onSuccess: (data) => {
      if (!data.error) {
        toast.success('Migration started successfully!');
        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.migration.active });
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard.activities() });
      } else {
        toast.error(data.error);
      }
    },
    onError: (error: Error) => {
      toast.error(`Failed to start migration: ${error.message}`);
    },
  });
};

export const useTranslateSQL = () => {
  return useMutation({
    mutationFn: ({ sql, sourceDb, targetDb }: { sql: string; sourceDb: string; targetDb: string }) =>
      migrationApi.translateSQL(sql, sourceDb, targetDb),
    onSuccess: (data) => {
      if (!data.error) {
        toast.success('SQL translated successfully!');
      } else {
        toast.error(data.error);
      }
    },
    onError: (error: Error) => {
      toast.error(`Translation failed: ${error.message}`);
    },
  });
};

export const useLogin = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (data) => {
      if (!data.error && data.data) {
        // Set token and invalidate user query
        queryClient.setQueryData(QUERY_KEYS.auth.currentUser, data.data.user);
        toast.success('Logged in successfully!');
      } else {
        toast.error(data.error || 'Login failed');
      }
    },
    onError: (error: Error) => {
      toast.error(`Login failed: ${error.message}`);
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear all cached data
      queryClient.clear();
      toast.success('Logged out successfully!');
    },
    onError: (error: Error) => {
      toast.error(`Logout failed: ${error.message}`);
    },
  });
};