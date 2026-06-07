export interface MetricCard {
  label: string;
  value: string;
  trend: string;
}

export interface RiskItem {
  title: string;
  detail: string;
  level: "高" | "中" | "低";
}

export interface DashboardSummary {
  metrics: MetricCard[];
  risks: RiskItem[];
}
