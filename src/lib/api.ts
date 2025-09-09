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