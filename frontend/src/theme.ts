import type { CriterionKey } from "./types";

/** Okabe-Ito colour-blind-safe palette. */
export const CRITERION_COLORS: Record<CriterionKey, string> = {
  performance_index: "#0072B2",
  impact_resistance: "#D55E00",
  max_service_temp: "#E69F00",
  cost: "#009E73",
  embodied_energy: "#CC79A7",
  recyclability: "#56B4E9",
};

export const CRITERION_SHORT: Record<CriterionKey, string> = {
  performance_index: "Performance per kg",
  impact_resistance: "Impact resistance",
  max_service_temp: "Service temperature",
  cost: "Low cost",
  embodied_energy: "Low embodied energy",
  recyclability: "Recyclability",
};

export const FAMILY_COLORS: Record<string, string> = {
  "printable-polymer": "#0072B2",
  "printable-composite": "#56B4E9",
  "fibre-composite": "#D55E00",
  metal: "#555555",
  "natural-core": "#009E73",
  recycled: "#CC79A7",
};

export const FAMILY_LABELS: Record<string, string> = {
  "printable-polymer": "Printable polymer",
  "printable-composite": "Printable composite",
  "fibre-composite": "Fibre composite",
  metal: "Metal",
  "natural-core": "Natural / core",
  recycled: "Recycled",
};

export const PROCESS_LABELS: Record<string, string> = {
  fdm: "3D printing (FDM)",
  layup: "Composite layup",
  machining: "Machining",
  injection: "Injection moulding",
  "sheet-forming": "Sheet forming",
  "cnc-cut": "CNC cutting",
};

export const CONFIDENCE_STYLE: Record<string, { cls: string; icon: string; help: string }> = {
  High: { cls: "bg-emerald-100 text-emerald-900 border-emerald-600", icon: "▲", help: "Its position barely changes when weights and data vary" },
  Medium: { cls: "bg-amber-100 text-amber-900 border-amber-600", icon: "◆", help: "Its position moves a fair amount when weights and data vary" },
  Low: { cls: "bg-orange-100 text-orange-900 border-orange-700", icon: "▼", help: "Its position changes a lot when weights and data vary" },
};

export const fmt = (x: number, digits = 2) => (Number.isFinite(x) ? x.toFixed(digits) : "-");
export const pct = (x: number) => `${Math.round(x * 100)}%`;
