export interface TrendPoint {
  date: string;
  category: string;
  count: number;
}

export interface PieSlice {
  name: string;
  value: number;
}

export interface MonthlyDuration {
  month: string;
  hours: number;
}

export interface DashboardStatsResponse {
  event_trend: TrendPoint[];
  event_category_distribution: PieSlice[];
  event_status_distribution: PieSlice[];
  average_resolution_hours: MonthlyDuration[];
  knowledge_cards: Array<{
    name: string;
    value: number;
  }>;
}

