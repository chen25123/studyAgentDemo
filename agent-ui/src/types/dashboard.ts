export interface Metric {
  label: string;
  value: string;
  trend: string;
}

export interface RiskItem {
  title: string;
  detail: string;
  level: "高" | "中" | "低";
}
