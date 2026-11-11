import type {
  AshbyResult, CompareResult, MaterialsDoc, Presets, Query, RankResult, RobResult,
} from "./types";

export class ApiError extends Error {}

async function parse(res: Response): Promise<unknown> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      if (typeof j.detail === "string") detail = j.detail;
      else if (Array.isArray(j.detail)) detail = j.detail.map((d: { loc?: unknown[]; msg: string }) => `${(d.loc ?? []).slice(1).join(".")}: ${d.msg}`).join("; ");
    } catch { /* keep default message */ }
    throw new ApiError(detail);
  }
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch {
    throw new ApiError("Could not reach the AirframeSelect server. Is the backend running on port 8000?");
  }
  return (await parse(res)) as T;
}

async function get<T>(path: string): Promise<T> {
  let res: Response;
  try { res = await fetch(path); } catch {
    throw new ApiError("Could not reach the AirframeSelect server. Is the backend running on port 8000?");
  }
  return (await parse(res)) as T;
}

/** Build the request body shared by rank / robustness / ashby / export endpoints. */
export function toRequest(q: Query) {
  return {
    part: q.part, profile: q.profile, method: q.method,
    weights: q.weights,
    constraints: q.constraints,
  };
}

export const api = {
  presets: () => get<Presets>("/api/presets"),
  materials: () => get<MaterialsDoc>("/api/materials"),
  rank: (q: Query) => post<RankResult>("/api/rank", toRequest(q)),
  robustness: (q: Query) => post<RobResult>("/api/robustness", toRequest(q)),
  ashby: (q: Query, axes: string, topN: number) => post<AshbyResult>("/api/ashby", { ...toRequest(q), axes, top_n: topN }),
  compare: (ids: string[], part: string) => post<CompareResult>("/api/compare", { material_ids: ids, part }),
  async download(kind: "csv" | "pdf", q: Query): Promise<void> {
    let res: Response;
    try {
      res = await fetch(`/api/export/${kind}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(toRequest(q)) });
    } catch { throw new ApiError("Could not reach the AirframeSelect server."); }
    if (!res.ok) await parse(res);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `airframeselect_${q.part}_${q.profile}.${kind}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};
