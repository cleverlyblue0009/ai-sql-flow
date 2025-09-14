/**
 * API configuration and utility functions
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic API fetch wrapper with error handling
 */
async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`API request to ${url} failed:`, error);
    throw error;
  }
}

/**
 * API endpoints
 */
export const api = {
  // Health check
  health: () => apiRequest<{ status: string; timestamp: number; mode: string }>('/health'),
  
  // Dashboard endpoints
  dashboard: {
    getOverview: () => apiRequest<{
      status: string;
      data: {
        timestamp: number;
        summary: {
          total_projects: number;
          total_data_profiles: number;
          recent_activity_count: number;
          success_rate: number;
          avg_quality_score: number;
          cost_savings: number;
        };
      };
    }>('/dashboard/comprehensive-overview'),
  },
  
  // Data Quality endpoints
  dataQuality: {
    getRecentUploads: () => apiRequest<{
      status: string;
      data: Array<{
        id: number;
        name: string;
        size: string;
        date: string;
        status: string;
        rows: number;
        columns: number;
        quality_score: number;
      }>;
    }>('/data-quality/recent-uploads'),
    
    uploadFile: async (formData: FormData) => {
      const url = `${API_BASE_URL}/data-quality/upload`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    },
    
    analyzeData: (data: {
      data_profile_id: number;
      project_id?: number;
      analysis_types: string[];
      ai_enabled: boolean;
      sample_size?: number;
    }) => apiRequest('/data-quality/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    
    getQualitySummary: (dataProfileId: number) => 
      apiRequest<{
        data_profile_id: number;
        file_name: string;
        overall_quality_score: number;
        quality_metrics: {
          completeness: { score: number; issues: number; status: string; description: string };
          accuracy: { score: number; issues: number; status: string; description: string };
          consistency: { score: number; issues: number; status: string; description: string };
          validity: { score: number; issues: number; status: string; description: string };
        };
        issue_breakdown: Array<{
          type: string;
          count: number;
          severity: string;
        }>;
        last_analyzed: string;
      }>(`/data-quality/quality-summary/${dataProfileId}`),
    
    startCleaning: (data: {
      data_profile_id: number;
      cleaning_operations: Array<{
        operation: string;
        parameters: Record<string, any>;
      }>;
      preview_only: boolean;
    }) => apiRequest('/data-quality/clean', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    
    getJobStatus: (jobId: string) => apiRequest<{
      job_id: string;
      status: string;
      progress_percentage: number;
      current_step: string;
      total_steps: number;
      started_at: string;
      result: any;
      error_message: string;
    }>(`/data-quality/status/${jobId}`),
  },
  
  // Monitoring endpoints
  monitoring: {
    getSystemMetrics: () => apiRequest<{
      status: string;
      data: {
        timestamp: number;
        cpu: { usage_percent: number; status: string };
        memory: { usage_percent: number; status: string };
        disk: { usage_percent: number; status: string };
      };
    }>('/monitoring/system'),
  },
};

export default api;