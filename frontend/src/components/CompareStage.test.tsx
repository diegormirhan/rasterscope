import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Scenario } from "../types";
import { CompareStage } from "./CompareStage";

vi.mock("../api", () => ({ inspectPixel: vi.fn() }));

const scenario: Scenario = {
  id: "test",
  name: "Test scene",
  location: "Test location",
  domain_shift: true,
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
  class_areas: [],
  transition_matrix: [],
  mean_uncertainty: { before: 0.2, after: 0.3 },
  source_type: "sentinel-2-stac",
  limitations: [],
};

describe("CompareStage", () => {
  it("drives the divider from the keyboard and reports its position", () => {
    render(<CompareStage scenario={scenario} layer="image" opacity={0.5} />);
    const divider = screen.getByRole("slider", { name: "Comparison divider" });

    expect(divider).toHaveAttribute("aria-valuenow", "50");

    fireEvent.keyDown(divider, { key: "ArrowRight" });
    expect(divider).toHaveAttribute("aria-valuenow", "52");

    fireEvent.keyDown(divider, { key: "ArrowLeft", shiftKey: true });
    expect(divider).toHaveAttribute("aria-valuenow", "42");

    fireEvent.keyDown(divider, { key: "Home" });
    expect(divider).toHaveAttribute("aria-valuenow", "0");

    // The divider is clamped, not wrapped: there is no image past the edge.
    fireEvent.keyDown(divider, { key: "ArrowLeft" });
    expect(divider).toHaveAttribute("aria-valuenow", "0");

    fireEvent.keyDown(divider, { key: "End" });
    expect(divider).toHaveAttribute("aria-valuenow", "100");
  });

  it("warns when the scene is outside the training distribution", () => {
    render(<CompareStage scenario={scenario} layer="mask" opacity={0.5} />);
    expect(screen.getByRole("note")).toHaveTextContent("Domain shift");
  });
});
