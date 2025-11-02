import axios from 'axios';

const API_BASE_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Haiku API
export const fetchHaikus = async (params = {}) => {
  const { data } = await api.get('/haikus', { params });
  return data;
};

export const fetchHaiku = async (id) => {
  const { data } = await api.get(`/haikus/${id}`);
  return data;
};

export const generateHaiku = async (filters = {}) => {
  const { data } = await api.post('/haikus/generate', filters);
  return data;
};

export const voteForHaiku = async (haikuId, username) => {
  const { data } = await api.post(`/haikus/${haikuId}/vote`, { username });
  return data;
};

// Lines API
export const fetchLines = async (params = {}) => {
  const { data } = await api.get('/lines', { params });
  return data;
};

// Statistics API
export const fetchStats = async () => {
  const { data } = await api.get('/stats');
  return data;
};

export const fetchLeaderboard = async (limit = 10) => {
  const { data } = await api.get('/leaderboard', { params: { limit } });
  return data;
};

// User API
export const fetchUserStats = async (username) => {
  const { data } = await api.get(`/users/${username}/stats`);
  return data;
};

export const fetchUserLines = async (username, params = {}) => {
  const { data } = await api.get(`/users/${username}/lines`, { params });
  return data;
};

export const fetchUserHaikus = async (username, params = {}) => {
  const { data } = await api.get(`/users/${username}/haikus`, { params });
  return data;
};

export default api;

