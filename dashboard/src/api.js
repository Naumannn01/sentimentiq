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
};