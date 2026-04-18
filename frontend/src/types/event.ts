import type { PaginatedData } from "./common";

export type EventCategory = "COMPLAINT" | "HAZARD" | "DISPUTE" | "VISIT" | "OTHER";
export type EventStatus = "PENDING" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

export interface EventItem {
  id: string;
  title: string;
  description: string;
  category: EventCategory;
  status: EventStatus;
  priority: number;
  address: string;
  reporter_name: string;
  resident_id?: string | null;
  ai_suggestion?: string | null;
  attachments: string[];
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

export interface EventCreatePayload {
  title: string;
  description: string;
  category: EventCategory;
  priority: number;
  address: string;
  reporter_name: string;
  resident_id?: string | null;
  ai_suggestion?: string | null;
  attachments: string[];
}

export interface EventUpdatePayload extends Partial<EventCreatePayload> {
  status?: EventStatus;
}

export interface EventAIAssistPayload {
  description: string;
}

export interface EventAIAssistResponse {
  suggested_category: EventCategory;
  suggested_priority: number;
  suggested_title: string;
  suggested_action: string;
  relevant_policy: string;
}

export type EventListResponse = PaginatedData<EventItem>;

