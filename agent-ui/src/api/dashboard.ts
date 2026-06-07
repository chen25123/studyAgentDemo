import { http } from "./http";
import type { DashboardSummary } from "../types/dashboard";

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await http.get<DashboardSummary>("/dashboard/summary");
  return response.data;
}
