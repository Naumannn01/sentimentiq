import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export const api = {
  getHotels: () =>
    axios.get(`${API_BASE}/hotels/`),

  getReviews: (params = {}) =>
    axios.get(`${API_BASE}/reviews/`, { params }),

  getHotelStats: (hotelName) =>
    axios.get(`${API_BASE}/stats/${encodeURIComponent(hotelName)}/`),

  getReview: (id) =>
    axios.get(`${API_BASE}/reviews/${id}/`),

  getWebhooks: () => axios.get(`${API_BASE}/webhooks/`),
  createWebhook: (data) => axios.post(`${API_BASE}/webhooks/`, data),
  updateWebhook: (id, data) => axios.patch(`${API_BASE}/webhooks/${id}/`, data),
  deleteWebhook: (id) => axios.delete(`${API_BASE}/webhooks/${id}/`),
  getWebhookLogs: (id) => axios.get(`${API_BASE}/webhooks/${id}/logs/`),
  getHotelTrend: (hotelName) =>
  axios.get(`${API_BASE}/stats/${encodeURIComponent(hotelName)}/trend/`),
};