import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

// Core connection configurations pointing to our FastAPI versioned router
const API_BASE_URL = "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Intercept Outgoing Requests: Inject Auth Bearer and Tenant Headers
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("organization_id");

    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    if (tenantId && config.headers) {
      config.headers["X-Organization-ID"] = tenantId;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept Incoming Responses: Token Auto-Refresh Retry Loop
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (!error.response) {
      return Promise.reject(error);
    }

    // Capture token expiration errors (401 Unauthorized)
    if (error.response.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue concurrent requests while token rotation executes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        isRefreshing = false;
        clearSessionAndRedirect();
        return Promise.reject(error);
      }

      try {
        // Execute dynamic token refresh handshake
        const response = await axios.post(`${API_BASE_URL}/auth/refresh?refresh_token_str=${refreshToken}`);
        const { access_token } = response.data;

        localStorage.setItem("access_token", access_token);
        api.defaults.headers.common.Authorization = `Bearer ${access_token}`;

        processQueue(null, access_token);
        isRefreshing = false;

        // Replay original request with refreshed token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        clearSessionAndRedirect();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

function clearSessionAndRedirect() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("organization_id");
  
  // Clean redirect back to standard login
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}
