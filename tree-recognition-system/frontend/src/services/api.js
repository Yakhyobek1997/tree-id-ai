/**
 * API Service
 * Handles all API calls to backend
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000,
});

// Tree registration
export const registerTree = async (formData) => {
  const response = await api.post('/register-tree', formData);
  return response.data;
};

// Tree identification
export const identifyTree = async (formData) => {
  const response = await api.post('/identify-tree', formData);
  return response.data;
};

export const analyzeTree = async (formData) => {
  const response = await api.post('/analyze-tree', formData);
  return response.data;
};

export const getAnalysisCapabilities = async () => {
  const response = await api.get('/analysis/capabilities');
  return response.data;
};

// Get all trees
export const getTrees = async (limit = 100, offset = 0) => {
  const response = await api.get('/trees', {
    params: { limit, offset }
  });
  return response.data;
};

// Get single tree
export const getTree = async (treeId, includeObservations = false) => {
  const response = await api.get(`/trees/${treeId}`, {
    params: { include_observations: includeObservations }
  });
  return response.data;
};

// Add observation
export const addObservation = async (treeId, formData) => {
  const response = await api.post(`/trees/${treeId}/observations`, formData);
  return response.data;
};

// Get observations
export const getObservations = async (treeId, limit = 100) => {
  const response = await api.get(`/trees/${treeId}/observations`, {
    params: { limit }
  });
  return response.data;
};

// Delete tree
export const deleteTree = async (treeId) => {
  const response = await api.delete(`/trees/${treeId}`);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
