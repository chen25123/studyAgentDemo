import axios from "axios";

export const http = axios.create({
  baseURL: "/api",
  timeout: 60000,
});

// Admin 接口自动附加 X-Admin-Token
http.interceptors.request.use((config) => {
  if (config.url?.includes("/admin/")) {
    const token = import.meta.env.VITE_ADMIN_TOKEN;
    if (token) {
      config.headers["X-Admin-Token"] = token;
    }
  }
  return config;
});
