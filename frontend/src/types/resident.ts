import type { EventItem } from "./event";
import type { PaginatedData } from "./common";

export interface VisitRecord {
  id: string;
  resident_id: string;
  visitor_name: string;
  content: string;
  summary?: string | null;
  created_at: string;
}

export interface ResidentItem {
  id: string;
  name: string;
  id_number: string;
  phone: string;
  address: string;
  tags: string[];
  notes?: string | null;
  last_visit_at?: string | null;
  visit_count: number;
  created_at: string;
  updated_at: string;
}

export interface ResidentDetail extends ResidentItem {
  visits: VisitRecord[];
  related_events: EventItem[];
}

export interface ResidentCreatePayload {
  name: string;
  id_number: string;
  phone: string;
  address: string;
  tags: string[];
  notes?: string | null;
}

export interface ResidentUpdatePayload extends Partial<ResidentCreatePayload> {}

export interface VisitCreatePayload {
  visitor_name: string;
  content: string;
  summary?: string | null;
}

export interface VisitSuggestResponse {
  resident_id: string;
  suggestions: string[];
  risk_summary: string;
}

export type ResidentListResponse = PaginatedData<ResidentItem>;

