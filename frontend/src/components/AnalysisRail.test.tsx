import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Scenario } from "../types";
import { AnalysisRail } from "./AnalysisRail";

const scenario: Scenario = {
  id: "test",
  name: "Test scene",
  location: "Test location",
  domain_shift: false,
  note: "Test note",
  before: { item_id: "S2-before", datetime: "2020-01-01T00:00:00Z", cloud_cover: 1 },
  after: { item_id: "S2-after", datetime: "2024-01-01T00:00:00Z", cloud_cover: 2 },
  assets: {
    before: "/before.png",
    after: "/after.png",
    before_mask: "/before-mask.png",
    after_mask: "/after-mask.png",
    before_uncertainty: "/before-uncertainty.png",
    after_uncertainty: "/after-uncertainty.png",
  },
  area_unit: "hectares",
  class_areas: [{ id: 0, name: "Tree cover", short_name: "Trees", color: "green", before: 10, after: 12, delta: 2 }],
  transition_matrix: [[100]],
  mean_uncertainty: { before: 0.2, after: 0.3 },
  source_type: "sentinel-2-stac",
  limitations: ["Model-derived estimate."],
};

describe("AnalysisRail", () => {
  it("renders units, deltas, uncertainty, and limitations", () => {
    render(<AnalysisRail scenario={scenario} />);

    expect(screen.getByText("Area estimates")).toBeInTheDocument();
    expect(screen.getByText("+2.0")).toBeInTheDocument();
    expect(screen.getByLabelText("After mean uncertainty 30 percent")).toBeInTheDocument();
    expect(screen.getByText("Model-derived estimate.")).toBeInTheDocument();
  });
});

