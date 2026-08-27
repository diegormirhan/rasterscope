import { AlertTriangle, ArrowDownRight, ArrowUpRight, Minus, Ruler } from "lucide-react";

import type { ClassArea, Scenario } from "../types";

interface AnalysisRailProps {
  scenario: Scenario;
}

export function AnalysisRail({ scenario }: AnalysisRailProps) {
  return (
    <aside className="analysis-rail" aria-label="Change analysis">
      <section className="analysis-section analysis-section--summary">
        <div className="analysis-section__title">
          <h2>Area estimates</h2>
          <span className="unit-label">{scenario.area_unit === "hectares" ? "ha" : "px"}</span>
        </div>
        <div className="area-header" aria-hidden="true">
          <span>Class</span><span>Before</span><span>After</span><span>Delta</span>
        </div>
        <div className="area-list">
          {scenario.class_areas.map((item) => <AreaRow key={item.id} item={item} unit={scenario.area_unit} />)}
        </div>
      </section>

      <section className="analysis-section">
        <div className="analysis-section__title">
          <h2>Uncertainty</h2>
          <AlertTriangle aria-hidden="true" />
        </div>
        <UncertaintyBar label="Before" value={scenario.mean_uncertainty.before} />
        <UncertaintyBar label="After" value={scenario.mean_uncertainty.after} />
        <p className="analysis-note">Entropy across seven predicted classes. Lower is more decisive, not necessarily more correct.</p>
      </section>

      <section className="analysis-section">
        <div className="analysis-section__title">
          <h2>Transition matrix</h2>
          <Ruler aria-hidden="true" />
        </div>
        <TransitionMatrix scenario={scenario} />
      </section>

      <section className="analysis-section analysis-section--limits">
        <h2>Read with care</h2>
        <ul>{scenario.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
      </section>
    </aside>
  );
}

function AreaRow({ item, unit }: { item: ClassArea; unit: Scenario["area_unit"] }) {
  const DeltaIcon = item.delta > 0 ? ArrowUpRight : item.delta < 0 ? ArrowDownRight : Minus;
  return (
    <div className="area-row">
      <span className="area-row__name"><span className={`class-swatch class-swatch--${item.id}`} />{item.short_name}</span>
      <span>{formatValue(item.before, unit)}</span>
      <span>{formatValue(item.after, unit)}</span>
      <span className="area-row__delta" data-direction={item.delta > 0 ? "up" : item.delta < 0 ? "down" : "flat"}>
        <DeltaIcon aria-hidden="true" />{formatSigned(item.delta, unit)}
      </span>
    </div>
  );
}

function UncertaintyBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="uncertainty-row">
      <div><span>{label}</span><strong>{Math.round(value * 100)}%</strong></div>
      <div className="uncertainty-track" aria-label={`${label} mean uncertainty ${Math.round(value * 100)} percent`}>
        <span style={{ transform: `scaleX(${value})` }} />
      </div>
    </div>
  );
}

function TransitionMatrix({ scenario }: { scenario: Scenario }) {
  const maximum = Math.max(...scenario.transition_matrix.flat(), 1);
  return (
    <div className="matrix" role="table" aria-label="Predicted land-cover transition matrix">
      <div className="matrix__corner" aria-hidden="true">From ↓ / To →</div>
      {scenario.class_areas.map((item) => (
        <div key={`head-${item.id}`} className="matrix__head" role="columnheader" title={item.name}>
          <span className={`class-swatch class-swatch--${item.id}`} />
        </div>
      ))}
      {scenario.transition_matrix.map((row, rowIndex) => (
        <div className="matrix__row" role="row" key={scenario.class_areas[rowIndex].id}>
          <div className="matrix__head matrix__head--row" role="rowheader" title={scenario.class_areas[rowIndex].name}>
            <span className={`class-swatch class-swatch--${scenario.class_areas[rowIndex].id}`} />
          </div>
          {row.map((value, columnIndex) => (
            <div
              className="matrix__cell"
              role="cell"
              key={`${rowIndex}-${columnIndex}`}
              style={{ "--intensity": Math.sqrt(value / maximum) } as React.CSSProperties}
              title={`${scenario.class_areas[rowIndex].name} to ${scenario.class_areas[columnIndex].name}: ${value.toLocaleString("en")}`}
            >
              {value > maximum * 0.08 ? compactNumber(value) : ""}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function formatValue(value: number, unit: Scenario["area_unit"]): string {
  return unit === "hectares" ? value.toFixed(1) : Math.round(value).toLocaleString("en");
}

function formatSigned(value: number, unit: Scenario["area_unit"]): string {
  const formatted = formatValue(Math.abs(value), unit);
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${formatted}`;
}

function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

