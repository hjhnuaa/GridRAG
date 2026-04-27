const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

// Axios 请求和 SSE 流式问答共用同一个基础地址，避免两处默认值漂移。
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/+$/, "");
