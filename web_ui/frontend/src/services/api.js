import axios from 'axios';

// API Configuration - Dynamic host detection
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};

const getWsBaseUrl = () => {
  const hostname = window.location.hostname;
  return `ws://${hostname}:8000`;
};

const API_BASE_URL = getApiBaseUrl();
const WS_BASE_URL = getWsBaseUrl();

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.message);
    
    // Handle specific error cases
    if (error.response?.status === 404) {
      throw new Error('Endpoint not found. Make sure the backend server is running.');
    } else if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (error.code === 'ECONNREFUSED') {
      throw new Error('Cannot connect to server. Make sure the backend is running on port 8000.');
    }
    
    throw error;
  }
);

/**
 * Fetch all available agents from the backend
 * @returns {Promise<Array>} Array of agent objects
 */
export const fetchAgents = async () => {
  try {
    const response = await api.get('/api/agents');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    throw new Error(`Failed to fetch agents: ${error.message}`);
  }
};

/**
 * Create WebSocket connection for agent terminal
 * @param {string} agentPath - Path to the agent file
 * @returns {WebSocket} WebSocket instance
 */
export const createAgentWebSocket = (agentPath) => {
  try {
    // Encode the agent path for URL safety
    const encodedPath = btoa(agentPath);
    const wsUrl = `${WS_BASE_URL}/api/ws/${encodedPath}`;
    
    console.log(`🔌 Creating WebSocket connection: ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    
    // Add connection event logging
    ws.addEventListener('open', () => {
      console.log('✅ WebSocket connected');
    });
    
    ws.addEventListener('close', (event) => {
      console.log(`🔌 WebSocket closed: ${event.code} ${event.reason}`);
    });
    
    ws.addEventListener('error', (error) => {
      console.error('❌ WebSocket error:', error);
    });
    
    return ws;
  } catch (error) {
    console.error('Failed to create WebSocket:', error);
    throw new Error(`Failed to create WebSocket: ${error.message}`);
  }
};

/**
 * Check if the backend server is reachable
 * @returns {Promise<boolean>} True if server is reachable
 */
export const checkServerHealth = async () => {
  try {
    const response = await api.get('/');
    return response.status === 200;
  } catch (error) {
    console.error('Server health check failed:', error);
    return false;
  }
};

/**
 * Utility function to handle API errors gracefully
 * @param {Function} apiCall - The API function to call
 * @param {any} fallbackValue - Value to return on error
 * @returns {Promise<any>} API result or fallback value
 */
export const safeApiCall = async (apiCall, fallbackValue = null) => {
  try {
    return await apiCall();
  } catch (error) {
    console.error('Safe API call failed:', error);
    return fallbackValue;
  }
};

// Export API instance for direct use if needed
export { api };

// Export constants
export const API_ENDPOINTS = {
  AGENTS: '/api/agents',
  WEBSOCKET: '/api/ws',
};

export const CONNECTION_STATUS = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
}; 