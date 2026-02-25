import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";
const TOKEN_KEY = "token";

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem("user");
      window.location.assign("/login");
    }
    return Promise.reject(error);
  }
);

const handleResponse = (promise) =>
  promise.then((res) => res.data).catch((error) => {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error?.message ||
      "Something went wrong";
    const err = new Error(message);
    err.status = error?.response?.status;
    throw err;
  });

export const registerUser = (email, password) =>
  handleResponse(apiClient.post("/auth/register", { email, password }));

export const loginUser = (email, password) =>
  handleResponse(apiClient.post("/auth/login", { email, password }));

export const searchProducts = (query) =>
  handleResponse(
    apiClient.get("/search", {
      params: { query },
    })
  );

export default apiClient;
