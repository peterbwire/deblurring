import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_KEY_STORAGE_KEY = "forensiclear_api_key";

let apiKey =
  typeof window !== "undefined" ? window.localStorage.getItem(API_KEY_STORAGE_KEY) || "" : "";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  }
  return config;
});

export const getStoredApiKey = () => apiKey;

export const setApiKey = (nextKey) => {
  apiKey = nextKey.trim();
  if (typeof window !== "undefined") {
    if (apiKey) {
      window.localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
    } else {
      window.localStorage.removeItem(API_KEY_STORAGE_KEY);
    }
  }
};

export const absoluteUrl = (url) => {
  if (!url) {
    return "";
  }
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  return `${API_BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
};

export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return data;
};

export const startProcess = async (jobId, payload) => {
  const { data } = await api.post(`/process/${jobId}`, payload);
  return data;
};

export const getProcessStatus = async (jobId, runId) => {
  const { data } = await api.get(`/process/${jobId}/${runId}`);
  return data;
};

export const healthCheck = async () => {
  const { data } = await api.get("/health");
  return data;
};

export const getCurrentUser = async () => {
  const { data } = await api.get("/auth/me");
  return data;
};

export const getRecentJobs = async () => {
  const { data } = await api.get("/auth/jobs");
  return data;
};

export const getOpsMetrics = async () => {
  const { data } = await api.get("/ops/metrics");
  return data;
};

export const extractErrorMessage = (error) => {
  if (typeof error?.response?.data?.detail === "string") {
    return error.response.data.detail;
  }
  if (error?.response?.status === 401) {
    return "Authentication failed. Please check your API key.";
  }
  return error?.message || "The request could not be completed.";
};
