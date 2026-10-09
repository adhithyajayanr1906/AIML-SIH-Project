import axios from 'axios';

// By default FastAPI runs on port 8000
const API_BASE_URL = 'http://127.0.0.1:8000';

export const routeRecommend = async (origin, destination, preference) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/route/recommend`, {
      origin,
      destination,
      preference
    });
    return response.data;
  } catch (error) {
    if (error.response) return error.response.data;
    throw error;
  }
};

export const predictEnvironmentalRisk = async (data) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/predict/environmental-risk`, data);
    return response.data;
  } catch (error) {
    if (error.response) return error.response.data;
    throw error;
  }
};
