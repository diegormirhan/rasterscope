import { Download, ImagePlus } from "lucide-react";

import type { Layer, Scenario, ScenarioCatalog } from "../types";

interface ToolbarProps {
  catalog: ScenarioCatalog | null;
  selectedScenario: Scenario | null;
  layer: Layer;
  opacity: number;
  onScenarioChange: (scenario: Scenario) => void;
  onLayerChange: (layer: Layer) => void;
  onOpacityChange: (opacity: number) => void;
  onUpload: () => void;
}

const layers: Array<{ id: Layer; label: string }> = [
  { id: "image", label: "Image" },
  { id: "mask", label: "Classes" },
  { id: "uncertainty", label: "Uncertainty" },
];

export function Toolbar({
  catalog,
  selectedScenario,
  layer,
  opacity,
  onScenarioChange,
  onLayerChange,
  onOpacityChange,
  onUpload,
}: ToolbarProps) {
  return (
    <header className="toolbar">
      <div className="toolbar__group">
        <div className="scenario-control">
          <label htmlFor="scenario">Scenario</label>
          <select
            id="scenario"
            value={selectedScenario?.id ?? ""}
            onChange={(event) => {
              const scenario = catalog?.scenarios.find((item) => item.id === event.target.value);
              if (scenario) onScenarioChange(scenario);
            }}
            disabled={!catalog?.scenarios.length}
          >
            {catalog?.scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.name}
              </option>
            ))}
          </select>
        </div>
        <div className="layer-control">
          <span id="layer-label">Layer</span>
          <div className="segmented" role="group" aria-labelledby="layer-label">
            {layers.map((item) => (
              <button
                key={item.id}
                type="button"
                className="segmented-button"
                data-active={layer === item.id}
                aria-pressed={layer === item.id}
                onClick={() => onLayerChange(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        {/* The slider only reads once an overlay exists to fade. */}
        <label className="opacity-control" data-available={layer !== "image"}>
          <span>Overlay</span>
          <input
            type="range"
            min="0.15"
            max="0.9"
            step="0.05"
            value={opacity}
            disabled={layer === "image"}
            onChange={(event) => onOpacityChange(Number(event.target.value))}
          />
          <output>{Math.round(opacity * 100)}%</output>
        </label>
      </div>
      <div className="toolbar__actions">
        <button className="button button--secondary" type="button" title="Upload pair" onClick={onUpload}>
          <ImagePlus aria-hidden="true" />
          <span>Upload pair</span>
        </button>
        {selectedScenario && (
          <a
            className="button button--primary"
            href={`/api/scenarios/${selectedScenario.id}/report`}
            download
            title="Export report"
          >
            <Download aria-hidden="true" />
            <span>Export report</span>
          </a>
        )}
      </div>
    </header>
  );
}
