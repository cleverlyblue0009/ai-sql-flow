// API Configuration and Service Layer
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface DashboardMetrics {
  data_quality_score: number;
  active_migrations: number;
  success_rate: number;
  cost_savings: number;
  tables_processed_today: number;
  change_data_quality: string;
  change_migrations: string;
  change_success_rate: string;
  change_cost_savings: string;
}

export interface ActivityItem {
  id: number;
  type: string;
  title: string;
  description?: string;
  timestamp: string;
  status: string;
  user?: string;
}

export interface QuickStats {
  files_uploaded_today: number;
  active_processes: number;
  avg_processing_time: number;
  error_rate: number;
}

export interface SystemStatus {
  overall_health: number;
  services: Array<{
    name: string;
    status: string;
    uptime: string;
    response_time: string;
  }>;
  performance: {
    cpu_usage: number;
    memory_usage: number;
    storage_usage: number;
    active_users: number;
  };
}

export interface DashboardOverview {
  metrics: DashboardMetrics;
  activities: ActivityItem[];
  quick_stats: QuickStats;
  system_status: SystemStatus;
}

// HTTP Client Class
class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    // Try to get token from localStorage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    try {
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          error: errorData.message || errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'An unexpected error occurred',
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      return this.handleResponse<T>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error occurred',
      };
    }
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      });

      return this.handleResponse<T>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error occurred',
      };
    }
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      });

      return this.handleResponse<T>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error occurred',
      };
    }
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'DELETE',
        headers: this.getHeaders(),
      });

      return this.handleResponse<T>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error occurred',
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.get('/health');
  }

  // System info
  async getSystemInfo(): Promise<ApiResponse<any>> {
    return this.get('/info');
  }
}

// Create and export API client instance
export const apiClient = new ApiClient();

// Dashboard API Functions
export const dashboardApi = {
  // Get dashboard overview (all data in one call)
  getOverview: (): Promise<ApiResponse<DashboardOverview>> =>
    apiClient.get('/dashboard/overview'),

  // Get individual dashboard components
  getMetrics: (): Promise<ApiResponse<DashboardMetrics>> =>
    apiClient.get('/dashboard/metrics'),

  getActivities: (limit: number = 20): Promise<ApiResponse<{ activities: ActivityItem[]; total: number }>> =>
    apiClient.get(`/dashboard/activities?limit=${limit}`),

  getQuickStats: (): Promise<ApiResponse<QuickStats>> =>
    apiClient.get('/dashboard/quick-stats'),

  getSystemStatus: (): Promise<ApiResponse<SystemStatus>> =>
    apiClient.get('/dashboard/system-status'),

  getPerformanceTrends: (days: number = 30): Promise<ApiResponse<any>> =>
    apiClient.get(`/dashboard/performance-trends?days=${days}`),

  getCostAnalysis: (): Promise<ApiResponse<any>> =>
    apiClient.get('/dashboard/cost-analysis'),
};

// Data Quality API Functions
export const dataQualityApi = {
  // File upload
  uploadFile: (file: File, options?: any): Promise<ApiResponse<any>> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      formData.append('options', JSON.stringify(options));
    }

    return fetch(`${API_BASE_URL}/data-quality/upload`, {
      method: 'POST',
      headers: {
        Authorization: apiClient.token ? `Bearer ${apiClient.token}` : '',
      },
      body: formData,
    }).then(response => apiClient['handleResponse'](response));
  },

  // Get analysis results
  getAnalysis: (fileId: string): Promise<ApiResponse<any>> =>
    apiClient.get(`/data-quality/analysis/${fileId}`),

  // Start cleaning process
  startCleaning: (fileId: string, config: any): Promise<ApiResponse<any>> =>
    apiClient.post(`/data-quality/clean/${fileId}`, config),

  // Get cleaning results
  getCleaningResults: (jobId: string): Promise<ApiResponse<any>> =>
    apiClient.get(`/data-quality/results/${jobId}`),

  // List recent uploads
  getRecentUploads: (limit: number = 10): Promise<ApiResponse<any>> =>
    apiClient.get(`/data-quality/uploads?limit=${limit}`),
};

// Migration API Functions
export const migrationApi = {
  // Start new migration
  startMigration: (config: any): Promise<ApiResponse<any>> =>
    apiClient.post('/migration/start', config),

  // Get migration status
  getMigrationStatus: (migrationId: string): Promise<ApiResponse<any>> =>
    apiClient.get(`/migration/status/${migrationId}`),

  // Translate SQL
  translateSQL: (sql: string, sourceDb: string, targetDb: string): Promise<ApiResponse<any>> =>
    apiClient.post('/migration/translate', { sql, source_db: sourceDb, target_db: targetDb }),

  // Get active migrations
  getActiveMigrations: (): Promise<ApiResponse<any>> =>
    apiClient.get('/migration/active'),

  // Get migration history
  getMigrationHistory: (limit: number = 20): Promise<ApiResponse<any>> =>
    apiClient.get(`/migration/history?limit=${limit}`),
};

// Authentication API Functions
export const authApi = {
  // Login
  login: (email: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string; user: any }>> =>
    apiClient.post('/auth/login', { username: email, password }),

  // Register
  register: (userData: any): Promise<ApiResponse<any>> =>
    apiClient.post('/auth/register', userData),

  // Get current user
  getCurrentUser: (): Promise<ApiResponse<any>> =>
    apiClient.get('/auth/me'),

  // Logout
  logout: (): Promise<ApiResponse<any>> =>
    apiClient.post('/auth/logout'),

  // Refresh token
  refreshToken: (refreshToken: string): Promise<ApiResponse<any>> =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
};

// Utility function to check if API is available
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await apiClient.healthCheck();
    return !response.error;
  } catch {
    return false;
  }
};

// Export the API client for custom usage
export default apiClient;