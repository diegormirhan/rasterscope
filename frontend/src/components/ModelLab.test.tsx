import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { MetricSet, ModelCatalog } from "../types";
import { ModelLab } from "./ModelLab";

const metric = (meanIou: number): MetricSet => ({
  mean_iou: meanIou,
  mean_dice: 0.5,
  pixel_accuracy: 0.8,
  expected_calibration_error: 0.07,
  per_class: [{ name: "Tree cover", iou: meanIou, dice: 0.6 }],
  confusion_matrix: [[100]],
});

const models: ModelCatalog = {
  baseline: { model: "baseline", created_at: "2026-01-01", test_metrics: metric(0.2) },
  unet: { model: "unet", created_at: "2026-01-01", metrics: metric(0.4) },
};

describe("ModelLab", () => {
  it("shows measured improvement and model limitations", () => {
    render(<ModelLab models={models} isLoading={false} />);

    expect(screen.getByText("+100%")).toBeInTheDocument();
    expect(screen.getByText("Compact U-Net")).toBeInTheDocument();
    expect(screen.getByText("What the aggregate hides")).toBeInTheDocument();
  });
});

