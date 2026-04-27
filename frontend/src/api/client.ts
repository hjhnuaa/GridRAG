import axios from "axios";

import type { ApiResponse } from "../types/common";
import { API_BASE_URL } from "./config";

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
