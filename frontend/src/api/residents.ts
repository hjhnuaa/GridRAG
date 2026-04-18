import type {
  ResidentCreatePayload,
  ResidentDetail,
  ResidentItem,
  ResidentListResponse,
  ResidentUpdatePayload,
  VisitCreatePayload,
  VisitRecord,
  VisitSuggestResponse
} from "../types/resident";
import { apiClient, unwrapResponse } from "./client";

export async function fetchResidents(params: {
  page?: number;
  page_size?: number;
  tags?: string;
}): Promise<ResidentListResponse> {
  return unwrapResponse(apiClient.get("/residents", { params }));
}

export async function createResident(payload: ResidentCreatePayload): Promise<ResidentItem> {
  return unwrapResponse(apiClient.post("/residents", payload));
}

export async function updateResident(residentId: string, payload: ResidentUpdatePayload): Promise<ResidentItem> {
  return unwrapResponse(apiClient.patch(`/residents/${residentId}`, payload));
}

export async function fetchResidentDetail(residentId: string): Promise<ResidentDetail> {
  return unwrapResponse(apiClient.get(`/residents/${residentId}`));
}

export async function createVisit(residentId: string, payload: VisitCreatePayload): Promise<VisitRecord> {
  return unwrapResponse(apiClient.post(`/residents/${residentId}/visit`, payload));
}

export async function fetchVisitSuggest(residentId: string): Promise<VisitSuggestResponse> {
  return unwrapResponse(apiClient.get(`/residents/${residentId}/visit-suggest`));
}

