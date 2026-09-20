import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
});

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (detail) return String(detail);
    if (error.response?.status) return `Request failed (${error.response.status}).`;
    if (error.message) return error.message;
  }
  return 'Request failed. Please try again.';
}

export const campaigns = () => api.get('/api/campaigns', { params: { _: Date.now() } }).then(r => r.data);
export const createCampaign = (data: unknown) => api.post('/api/campaigns', data).then(r => r.data);
export const runCampaign = (id: number, wait = false) => api.post(`/api/campaigns/${id}/run`, null, { params: { wait } }).then(r => r.data);
export const stopCampaign = (id: number) => api.post(`/api/campaigns/${id}/stop`).then(r => r.data);
export const deleteCampaign = (id: number) => api.delete(`/api/campaigns/${id}`).then(r => r.data);
export const campaignStatus = (id: number) => api.get(`/api/campaigns/${id}/status`).then(r => r.data);
export const content = (id: number) => api.get(`/api/campaigns/${id}/content`).then(r => r.data);
export const research = (id: number) => api.get(`/api/campaigns/${id}/research`).then(r => r.data);
export const strategy = (id: number) => api.get(`/api/campaigns/${id}/strategy`).then(r => r.data);
export const calendar = (id: number) => api.get(`/api/campaigns/${id}/calendar`).then(r => r.data);
export const report = (id: number) => api.get(`/api/campaigns/${id}/report`).then(r => r.data);
export const approve = (id: number, comment = '') => api.post(`/api/content/${id}/approve`, { comment }).then(r => r.data);
export const reject = (id: number, comment = 'Needs revision') => api.post(`/api/content/${id}/reject`, { comment }).then(r => r.data);
export const regenerate = (id: number) => api.post(`/api/content/${id}/regenerate`).then(r => r.data);
export const editContent = (id: number, body: string) => api.put(`/api/content/${id}`, { body }).then(r => r.data);
export const publish = (id: number) => api.post(`/api/content/${id}/publish`).then(r => r.data);
export const analytics = (id: number, data: unknown) => api.post(`/api/campaigns/${id}/analytics`, data).then(r => r.data);
export const analyticsUpload = (id: number, file: File, targets: Record<string, number>) => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('targets', JSON.stringify(targets));
  return api.post(`/api/campaigns/${id}/analytics/upload`, fd).then(r => r.data);
};
