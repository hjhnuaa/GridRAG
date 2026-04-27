import axios from "axios";

import type { ApiResponse } from "../types/common";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

// 普通请求和 SSE 流式问答共用同一个基础地址，避免默认值分散在多个文件里。
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/+$/, "");

const apiClient = axios.create({
  baseURL: API_BASE_URL,
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
