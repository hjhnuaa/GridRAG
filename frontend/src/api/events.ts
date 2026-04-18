import type {
  EventAIAssistPayload,
  EventAIAssistResponse,
  EventCreatePayload,
  EventItem,
  EventListResponse,
  EventUpdatePayload
} from "../types/event";
import { apiClient, unwrapResponse } from "./client";

export interface EventListParams {
  page?: number;
  page_size?: number;
  status?: string;
  category?: string;
  keyword?: string;
}

export async function fetchEvents(params: EventListParams): Promise<EventListResponse> {
  return unwrapResponse(apiClient.get("/events", { params }));
}

export async function createEvent(payload: EventCreatePayload): Promise<EventItem> {
  return unwrapResponse(apiClient.post("/events", payload));
}

export async function updateEvent(eventId: string, payload: EventUpdatePayload): Promise<EventItem> {
  return unwrapResponse(apiClient.patch(`/events/${eventId}`, payload));
}

export async function closeEvent(eventId: string): Promise<EventItem> {
  return unwrapResponse(apiClient.post(`/events/${eventId}/close`));
}

export async function fetchEventDetail(eventId: string): Promise<EventItem> {
  return unwrapResponse(apiClient.get(`/events/${eventId}`));
}

export async function fetchEventAIAssist(payload: EventAIAssistPayload): Promise<EventAIAssistResponse> {
  return unwrapResponse(apiClient.post("/events/ai-assist", payload));
}

