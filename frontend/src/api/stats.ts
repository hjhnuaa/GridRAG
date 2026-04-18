import type { DashboardStatsResponse } from "../types/stats";
import { apiClient, unwrapResponse } from "./client";

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  return unwrapResponse(apiClient.get("/stats/dashboard"));
}

