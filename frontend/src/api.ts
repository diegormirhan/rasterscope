import type { ModelCatalog, Phase, PixelInspection, Scenario, ScenarioCatalog } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: "The server returned an invalid response." }));
    throw new Error(detail.detail ?? `Request failed with status ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export function fetchScenarios(): Promise<ScenarioCatalog> {
  return request<ScenarioCatalog>("/api/scenarios");
}

export function fetchModels(): Promise<ModelCatalog> {
  return request<ModelCatalog>("/api/models");
}

export function inspectPixel(
  scenarioId: string,
  phase: Phase,
  x: number,
  y: number,
): Promise<PixelInspection> {
  const query = new URLSearchParams({ phase, x: String(x), y: String(y) });
  return request<PixelInspection>(`/api/scenarios/${scenarioId}/inspect?${query}`);
}

export function analyzePair(before: File, after: File): Promise<Scenario> {
  const body = new FormData();
  body.append("before", before);
  body.append("after", after);
  return request<Scenario>("/api/analyze", { method: "POST", body });
}
