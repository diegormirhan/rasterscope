export type Surface = "compare" | "model-lab" | "about";
export type Layer = "image" | "mask" | "uncertainty";
export type Phase = "before" | "after";

export interface SourceMetadata {
  item_id: string;
  datetime: string | null;
  cloud_cover: number | null;
  platform?: string;
}

export interface ScenarioAssets {
  before: string;
  after: string;
  before_mask: string;
  after_mask: string;
  before_uncertainty: string;
  after_uncertainty: string;
}

export interface ClassArea {
  id: number;
  name: string;
  short_name: string;
  color: string;
  before: number;
  after: number;
  delta: number;
}

export interface Scenario {
  id: string;
  name: string;
  location: string;
  domain_shift: boolean;
  note: string;
  before: SourceMetadata;
  after: SourceMetadata;
  assets: ScenarioAssets;
  area_unit: "hectares" | "pixels";
  class_areas: ClassArea[];
  transition_matrix: number[][];
  mean_uncertainty: { before: number; after: number };
  source_type: string;
  limitations: string[];
}

export interface ScenarioCatalog {
  generated_at: string;
  model: string;
  scenarios: Scenario[];
}

export interface ClassMetric {
  name: string;
  iou: number;
  dice: number;
}

export interface MetricSet {
  mean_iou: number;
  mean_dice: number;
  pixel_accuracy: number;
  expected_calibration_error: number | null;
  per_class: ClassMetric[];
  confusion_matrix: number[][];
}

export interface ModelRecord {
  model: string;
  created_at: string;
  test_metrics?: MetricSet;
  metrics?: MetricSet;
}

export interface ModelCatalog {
  baseline: ModelRecord;
  unet: ModelRecord;
}

export interface PixelInspection {
  x: number;
  y: number;
  phase: Phase;
  class_id: number;
  class_name: string;
  color: string;
  confidence: number;
  uncertainty: number;
}

