// API 客户端配置
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 — 自动携带 JWT Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    // 401 未认证，清除 token 并跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }

    let message = error.message || '请求失败';
    const respData = error.response?.data;

    if (respData) {
      if (respData instanceof Blob) {
        // Blob 类型响应（导出 API 等），读取文本提取后端错误详情
        try {
          const text = await respData.text();
          const parsed = JSON.parse(text);
          message = parsed.detail || message;
        } catch {
          // 无法解析则使用默认错误消息
        }
      } else if (typeof respData === 'object' && respData.detail) {
        // FastAPI JSON 错误响应 {"detail": "..."}
        message = respData.detail;
      } else if (typeof respData === 'string' && respData.length > 0 && respData.length < 200) {
        // 纯文本错误响应（如 "Internal Server Error"）
        message = respData;
      }
    }

    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

// ===== 班级 API =====
export const classApi = {
  list: (params?: any) => apiClient.get('/classes/', { params }),
  get: (id: number) => apiClient.get(`/classes/${id}`),
  create: (data: any) => apiClient.post('/classes/', data),
  update: (id: number, data: any) => apiClient.put(`/classes/${id}`, data),
  delete: (id: number) => apiClient.delete(`/classes/${id}`),
};

// ===== 教师 API =====
export const teacherApi = {
  list: (params?: any) => apiClient.get('/teachers/', { params }),
  get: (id: number) => apiClient.get(`/teachers/${id}`),
  create: (data: any) => apiClient.post('/teachers/', data),
  update: (id: number, data: any) => apiClient.put(`/teachers/${id}`, data),
  delete: (id: number) => apiClient.delete(`/teachers/${id}`),
};

// ===== 课程 API =====
export const courseApi = {
  list: (params?: any) => apiClient.get('/courses/', { params }),
  get: (id: number) => apiClient.get(`/courses/${id}`),
  create: (data: any) => apiClient.post('/courses/', data),
  update: (id: number, data: any) => apiClient.put(`/courses/${id}`, data),
  delete: (id: number) => apiClient.delete(`/courses/${id}`),
};

// ===== 教室 API =====
export const classroomApi = {
  list: (params?: any) => apiClient.get('/classrooms/', { params }),
  get: (id: number) => apiClient.get(`/classrooms/${id}`),
  create: (data: any) => apiClient.post('/classrooms/', data),
  update: (id: number, data: any) => apiClient.put(`/classrooms/${id}`, data),
  delete: (id: number) => apiClient.delete(`/classrooms/${id}`),
};

// ===== 排课 API =====
export const scheduleApi = {
  generate: (data: any) => apiClient.post('/schedules/generate', data),
  list: (params?: any) => apiClient.get('/schedules/', { params }),
  update: (id: number, data: any) => apiClient.put(`/schedules/${id}`, data),
  delete: (id: number) => apiClient.delete(`/schedules/${id}`),
  deleteVersion: (version: string) => apiClient.delete(`/schedules/version/${version}`),
  getVersions: () => apiClient.get('/schedules/versions'),
  getConflicts: (version?: string) => apiClient.get('/schedules/conflicts', { params: { version } }),
  getExplanation: (version?: string) => apiClient.get('/schedules/explanation', { params: { version } }),
};

// ===== 约束 API =====
export const constraintApi = {
  list: (params?: any) => apiClient.get('/constraints/', { params }),
  getDefaults: () => apiClient.get('/constraints/defaults'),
  get: (id: number) => apiClient.get(`/constraints/${id}`),
  create: (data: any) => apiClient.post('/constraints/', data),
  update: (id: number, data: any) => apiClient.put(`/constraints/${id}`, data),
  delete: (id: number) => apiClient.delete(`/constraints/${id}`),
  learn: () => apiClient.post('/constraints/learn'),
};

// ===== 导入导出 API =====
export const ioApi = {
  downloadTemplate: (entityType: string) =>
    apiClient.get(`/io/template/${entityType}`, { responseType: 'blob' }),
  importCsv: (entityType: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/io/csv/${entityType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  exportExcel: (version?: string) =>
    apiClient.get('/io/export/excel', { params: { version }, responseType: 'blob' }),
  exportPdf: (version?: string, viewType?: string) =>
    apiClient.get('/io/export/pdf', { params: { version, view_type: viewType }, responseType: 'blob' }),
  getReport: (version?: string) => apiClient.get('/io/report', { params: { version } }),
};

// ===== 认证 API =====
export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    apiClient.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    apiClient.post('/auth/login', data),
  getMe: () => apiClient.get('/auth/me'),
};
