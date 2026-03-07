import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8008/api',
})

// Add request interceptor for auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle specific error statuses
      if (error.response.status === 401) {
        // Handle unauthorized
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const experimentService = {
  getAll: () => api.get('/experiments'),
  getById: (id) => api.get(`/experiments/${id}`),
  create: (experimentData) => api.post('/experiments', experimentData),
  update: (id, updateData) => api.put(`/experiments/${id}`, updateData),
  getResults: (id) => api.get(`/experiments/${id}/results`),
  addResult: (id, resultData) => api.post(`/experiments/${id}/results`, resultData),
  run: (id) => api.post(`/experiments/${id}/run`),
  cancel: (id) => api.post(`/experiments/${id}/cancel`),
  delete: (id) => api.post(`/experiments/${id}/delete`),
  restart: (id) => api.post(`/experiments/${id}/restart`),
  batchActions: (actionData) => api.post('/experiments/actions', actionData),
}

export const architectureService = {
  getAll: () => api.get('/architectures'),
  getByName: (name) => api.get(`/architectures/view/${name}`),
  create: (architectureData) => api.post('/architectures', architectureData),
  getRegistry: () => api.get('/architectures/registry'),
}

export const datasetService = {
  getAll: () => api.get('/datasets'),
}

export const healthService = {
  check: () => api.get('/health'),
}

export default api
