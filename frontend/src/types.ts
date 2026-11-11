export type Method = "topsis" | "wsm";
export type CriterionKey =
  | "performance_index"
  | "impact_resistance"
  | "max_service_temp"
  | "cost"
  | "embodied_energy"
  | "recyclability";

export const CRITERIA: CriterionKey[] = [
  "performance_index",
  "impact_resistance",
  "max_service_temp",
  "cost",
  "embodied_energy",
  "recyclability",
];

export interface CriterionMeta { key: CriterionKey; label: string; direction: "benefit" | "cost"; plain: string }
export interface Constraints {
  max_density_kg_m3: number | null;
  min_strength_MPa: number | null;
  min_service_temp_C: number | null;
  max_cost_usd_per_kg: number | null;
  required_process: string | null;
}
export interface Part {
  id: string; name: string; load_case: string; performance_index: string; constraints: Constraints;
  weights: Record<CriterionKey, number>; allowed_processes: string[]; rationale: string;
}
export interface Profile { id: string; name: string; description: string; modifiers: Record<CriterionKey, number> }
export interface Scenario {
  id: string; name: string; part: string; profile: string; description: string;
  constraint_overrides: Partial<Constraints>;
}
export interface Presets {
  criteria: CriterionMeta[];
  indices: Record<string, { label: string; formula: string; plain: string }>;
  parts: Part[]; profiles: Profile[]; scenarios: Scenario[];
}

export interface Range { min: number; max: number }
export interface MaterialRecord {
  id: string; name: string; family: string; processes: string[]; notes: string; caveat?: string;
  property_basis: string; data_status: string;
  properties: Record<string, Range>; scores: { impact_resistance: number; recyclability: number };
}
export interface MaterialsDoc { disclaimer: string; units: Record<string, string>; materials: MaterialRecord[] }

export interface RankRow {
  rank: number; id: string; name: string; family: string; processes: string[];
  score: number; topsis_score: number; wsm_score: number; topsis_rank: number; wsm_rank: number;
  performance_index: { min: number; mid: number; max: number };
  values: Record<string, number>;
  flags: string[]; contributions: Record<CriterionKey, number>;
  explanation: string; strengths: CriterionKey[]; weaknesses: CriterionKey[]; notes: string; caveat: string | null;
}
export interface Agreement { top1_agree: boolean; top3_agree: boolean; top3_overlap: number; spearman: number }
export interface Excluded { id: string; name: string; family: string; reasons: string[] }
export interface ResolvedInputs {
  part: { id: string; name: string; load_case: string; rationale: string };
  profile: { id: string; name: string; description: string };
  weights: Record<CriterionKey, number>;
  constraints: Constraints;
  performance_index: { id: string; label: string; formula: string; units: string };
  method: Method;
}
export interface RankResult {
  inputs: ResolvedInputs; n_total: number; n_candidates: number; excluded: Excluded[];
  ranking: RankRow[]; agreement: Agreement | null; message: string | null;
}
export interface RobRow {
  id: string; name: string; family: string; baseline_rank: number; p_rank1: number; p_top3: number;
  median_rank: number; rank_p05: number; rank_p95: number; stability: number;
  confidence: "High" | "Medium" | "Low"; rank_distribution: number[];
}
export interface RobResult {
  settings: { trials: number; seed: number; concentration: number | null; range_scale: number; method: Method };
  materials: RobRow[]; summary?: string; message: string | null;
  winner: { baseline_top_id: string; baseline_top_name: string; baseline_top_p_rank1: number;
            most_likely_id: string; most_likely_name: string; most_likely_p_rank1: number } | null;
}
export interface AshbyPoint {
  id: string; name: string; family: string; x: { min: number; max: number; mid: number };
  y: { min: number; max: number; mid: number }; excluded: boolean; rank: number | null; top: boolean;
}
export interface AshbyResult {
  axes: string; x: { property: string; label: string; unit: string }; y: { property: string; label: string; unit: string };
  performance_index: { id: string; label: string; formula: string; units: string };
  points: AshbyPoint[];
  guide: { slope: number; intercept: number; index_value: number; description: string; through: string; index: string } | null;
  top_ids: string[]; message: string | null;
}
export interface CompareResult {
  performance_index: string; criteria: CriterionKey[];
  materials: { id: string; name: string; family: string; normalized: Record<CriterionKey, number>;
               raw: Record<CriterionKey, number>; density_kg_m3: number; youngs_modulus_GPa: number;
               tensile_strength_MPa: number; notes: string; property_basis: string }[];
}

/** Everything the user chooses in the selector; maps 1:1 onto the API request. */
export interface Query {
  part: string; profile: string; method: Method;
  weights: Record<CriterionKey, number>; // raw slider values 0..100
  constraints: Constraints;
}

export interface ParetoPoint { id: string; name: string; family: string; rank: number; x: number; y: number; pareto: boolean; dominated_by: string | null }
export interface ParetoResult {
  x: { key: CriterionKey; label: string; direction: "benefit" | "cost" };
  y: { key: CriterionKey; label: string; direction: "benefit" | "cost" };
  points: ParetoPoint[]; front_ids: string[]; message: string | null;
}
export interface ParsedRequirement {
  part: string | null; profile: string | null; constraints: Partial<Constraints>;
  matches: { field: string; value: string | number; because: string }[]; notes: string[];
}
