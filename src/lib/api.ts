/**
 * API configuration and utility functions
 */
import { auth } from './firebase';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get Firebase ID token for authenticated requests
 * Returns null if user is not authenticated (which is ok - backend handles demo users)
 */
async function getAuthToken(): Promise<string | null> {
  try {
    // Check if Firebase auth is initialized
    if (!auth) {
      return null;
    }
    
    const currentUser = auth.currentUser;
    if (currentUser) {
      return await currentUser.getIdToken();
    }
    return null;
  } catch (error) {
    // Silent failure - authentication is optional
    console.debug('No Firebase token available (this is ok):', error);
    return null;
  }
}

/**
 * Generic API fetch wrapper with error handling and optional Firebase authentication
 * Authentication is optional - backend uses demo users if no token is provided
 */
async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    // Get Firebase token for authentication (optional)
    const token = await getAuthToken();
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API request failed: ${response.status} ${response.statusText}. ${errorText}`);
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
        has_cleaned_data?: boolean;
      }>;
    }>('/data-quality/recent-uploads'),
    
    uploadFile: async (formData: FormData) => {
      const url = `${API_BASE_URL}/data-quality/upload`;
      const token = await getAuthToken();
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
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
      project_id?: number;
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
    
    getValidationResults: (dataProfileId: number) => apiRequest<{
      data_profile_id: number;
      before_cleaning: {
        overall_quality_score: number;
        completeness: number;
        accuracy: number;
        consistency: number;
        validity: number;
        total_rows: number;
      };
      after_cleaning: {
        overall_quality_score: number;
        completeness: number;
        accuracy: number;
        consistency: number;
        validity: number;
        total_rows: number;
      };
      improvement: {
        overall_quality_score: number;
        completeness: number;
        accuracy: number;
        consistency: number;
        validity: number;
      };
      cleaning_summary: {
        operations_performed: string[];
        records_processed: number;
        records_removed: number;
        quality_improvement: number;
      };
    }>(`/data-quality/validation-results/${dataProfileId}`),
    
    getIssueDetails: (dataProfileId: number, issueType: string) => apiRequest<{
      issue_type: string;
      data_profile_id: number;
      file_name: string;
      total_count: number;
      severity: string;
      description: string;
      examples: string[];
      recommendations: string[];
    }>(`/data-quality/issue-details/${dataProfileId}/${encodeURIComponent(issueType)}`),
    
    exportCleanedData: async (dataProfileId: number) => {
      const url = `${API_BASE_URL}/data-quality/export-cleaned-data/${dataProfileId}`;
      const token = await getAuthToken();
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status} ${response.statusText}`);
      }
      
      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'cleaned_data.csv';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return { success: true, filename };
    },
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
    
    getApplicationMetrics: () => apiRequest<{
      status: string;
      data: any;
    }>('/monitoring/application'),
    
    getServiceStatus: () => apiRequest<{
      status: string;
      data: {
        services: Record<string, { status: string; uptime: string; response: string }>;
        overall_health: string;
      };
    }>('/monitoring/services'),
    
    getActiveAlerts: () => apiRequest<{
      status: string;
      data: {
        alerts: Array<{
          id: string;
          severity: string;
          title: string;
          description: string;
          timestamp: string;
          affected: string;
        }>;
        total_count: number;
        critical_count: number;
        warning_count: number;
        info_count: number;
      };
    }>('/monitoring/alerts'),
    
    acknowledgeAlert: (alertId: string) => apiRequest<{
      status: string;
      message: string;
    }>(`/monitoring/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    }),
    
    getRealtimeMetrics: () => apiRequest<{
      status: string;
      data: {
        timestamp: number;
        summary: {
          active_processes: number;
          success_rate: number;
          avg_response_time: number;
          error_rate: number;
          cpu_usage: number;
          memory_usage: number;
          active_alerts: number;
        };
        trends: Record<string, string>;
        service_count: {
          operational: number;
          degraded: number;
          error: number;
        };
      };
    }>('/monitoring/metrics/realtime'),
  },
  
  // Settings endpoints
  settings: {
    getDatabaseConnections: () => apiRequest<{
      status: string;
      data: {
        connections: Array<{
          id: number;
          name: string;
          type: string;
          host: string;
          status: string;
          lastTest: string;
        }>;
        total_count: number;
      };
    }>('/settings/database-connections'),
    
    testConnection: (connectionId: number) => apiRequest<{
      status: string;
      data: any;
    }>(`/settings/database-connections/${connectionId}/test`, {
      method: 'POST',
    }),
    
    getUserManagement: () => apiRequest<{
      status: string;
      data: {
        users: Array<{
          id: number;
          name: string;
          email: string;
          role: string;
          status: string;
          lastActive: string;
        }>;
        total_count: number;
      };
    }>('/settings/user-management'),
    
    getAIConfiguration: () => apiRequest<{
      status: string;
      data: any;
    }>('/settings/ai-configuration'),
    
    getIntegrations: () => apiRequest<{
      status: string;
      data: any;
    }>('/settings/integrations'),
    
    getSecuritySettings: () => apiRequest<{
      status: string;
      data: any;
    }>('/settings/security'),
  },
};

export default api;