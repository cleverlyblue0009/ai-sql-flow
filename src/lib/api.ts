import { auth } from './firebase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const currentUser = auth.currentUser;
    if (currentUser) {
      try {
        const token = await currentUser.getIdToken();
        headers['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        console.error('Failed to get auth token:', error);
      }
    }

    return headers;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = await this.getAuthHeaders();

    const config: RequestInit = {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async upload<T>(endpoint: string, file: File, additionalData?: Record<string, any>): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
      });
    }

    const headers = await this.getAuthHeaders();
    delete headers['Content-Type']; // Let browser set content-type for multipart/form-data

    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
      headers,
    });
  }

  // Authentication endpoints
  async authenticateWithFirebase(token: string) {
    return this.post('/auth/firebase-auth', { token });
  }

  async getCurrentUser() {
    return this.get('/auth/me');
  }

  async logout() {
    return this.post('/auth/logout');
  }

  // Data Quality endpoints
  async analyzeDataQuality(file: File, options?: any) {
    return this.upload('/data-quality/analyze', file, options);
  }

  async getDataQualityReport(reportId: string) {
    return this.get(`/data-quality/reports/${reportId}`);
  }

  async cleanData(reportId: string, cleaningOptions: any) {
    return this.post(`/data-quality/reports/${reportId}/clean`, cleaningOptions);
  }

  // SQL Migration endpoints
  async translateSQL(data: { sql: string; source_dialect: string; target_dialect: string }) {
    return this.post('/migration/translate', data);
  }

  async getMigrationJob(jobId: string) {
    return this.get(`/migration/jobs/${jobId}`);
  }

  // Dashboard endpoints
  async getDashboardMetrics() {
    return this.get('/dashboard/metrics');
  }

  async getRecentActivity() {
    return this.get('/dashboard/activity');
  }

  // WebSocket URL with auth token
  async getWebSocketUrl(path: string = ''): Promise<string> {
    const currentUser = auth.currentUser;
    if (!currentUser) {
      throw new Error('User not authenticated');
    }

    const token = await currentUser.getIdToken();
    const wsBaseUrl = API_BASE_URL.replace('http', 'ws').replace('/api', '');
    const url = new URL(`/ws${path}`, wsBaseUrl);
    url.searchParams.set('token', token);
    
    return url.toString();
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;