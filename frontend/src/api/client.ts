import axios from "axios";

import type { ApiResponse } from "../types/common";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 30000
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const message = error.response?.data?.message;
    return Promise.reject(new Error(typeof message === "string" ? message : "请求失败，请稍后重试。"));
  }
);

export async function unwrapResponse<T>(request: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const response = await request;
  return response.data.data;
}

export { apiClient };

