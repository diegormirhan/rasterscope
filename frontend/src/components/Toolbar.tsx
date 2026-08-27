import { Download, ImagePlus, Layers2 } from "lucide-react";

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
      <div className="layer-control" aria-label="Visible layer">
        <Layers2 aria-hidden="true" />
        {(["image", "mask", "uncertainty"] as const).map((item) => (
          <button
            key={item}
            className="segmented-button"
            data-active={layer === item}
            aria-pressed={layer === item}
            onClick={() => onLayerChange(item)}
          >
            {item === "image" ? "Image" : item === "mask" ? "Classes" : "Uncertainty"}
          </button>
        ))}
      </div>
      <label className="opacity-control">
        <span>Opacity</span>
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
      <div className="toolbar__actions">
        <button
          className="button button--secondary"
          aria-label="Upload pair"
          title="Upload pair"
          onClick={onUpload}
        >
          <ImagePlus aria-hidden="true" />
          <span>Upload pair</span>
        </button>
        {selectedScenario && (
          <a
            className="button button--primary"
            href={`/api/scenarios/${selectedScenario.id}/report`}
            download
            aria-label="Export report"
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
