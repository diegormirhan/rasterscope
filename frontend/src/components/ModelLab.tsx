import { AlertCircle, ArrowRight, CheckCircle2 } from "lucide-react";

import type { MetricSet, ModelCatalog } from "../types";
import { Matrix } from "./Matrix";

interface ModelLabProps {
  models: ModelCatalog | null;
  isLoading: boolean;
}

export function ModelLab({ models, isLoading }: ModelLabProps) {
  if (isLoading) {
    return <div className="model-lab model-lab--loading" aria-busy="true"><div className="skeleton skeleton--line" /><div className="skeleton skeleton--block" /></div>;
  }
  const baseline = models?.baseline.test_metrics;
  const unet = models?.unet.metrics;
  if (!baseline || !unet) {
    return (
      <section className="empty-state">
        <AlertCircle aria-hidden="true" />
        <h1>Evaluation artifacts are unavailable.</h1>
        <p>Run the baseline and U-Net evaluation commands, then reload this page.</p>
        <code>uv run rasterscope evaluate --model unet</code>
      </section>
    );
  }
  const improvement = ((unet.mean_iou / baseline.mean_iou - 1) * 100).toFixed(0);
  return (
    <article className="model-lab">
      <header className="model-lab__header">
        <div>
          <h1>Model evidence</h1>
          <p>A fixed test split, macro averages, and the classes the model does not learn.</p>
        </div>
        <div className="metric-callout">
          <span>mIoU lift over RGB baseline</span>
          <strong>+{improvement}%</strong>
        </div>
      </header>
      <section className="model-comparison" aria-label="Model comparison">
        <ModelSummary name="Color-centroid baseline" metrics={baseline} />
        <ArrowRight className="model-comparison__arrow" aria-hidden="true" />
        <ModelSummary name="Compact U-Net" metrics={unet} selected />
      </section>
      <section className="model-detail">
        <div className="per-class">
          <h2>Per-class performance</h2>
          <div className="metric-table" role="table">
            <div className="metric-table__header" role="row"><span>Class</span><span>IoU</span><span>Dice</span><span>Finding</span></div>
            {unet.per_class.map((item, index) => (
              <div className="metric-table__row" role="row" key={item.name}>
                <span><span className={`class-swatch class-swatch--${index}`} />{item.name}</span>
                <span className="metric-table__value" style={{ "--fill": item.iou } as React.CSSProperties}>
                  {formatMetric(item.iou)}
                </span>
                <span className="metric-table__value" style={{ "--fill": item.dice } as React.CSSProperties}>
                  {formatMetric(item.dice)}
                </span>
                <span className={item.iou === 0 ? "status status--warning" : "status"}>
                  {item.iou === 0 ? <AlertCircle aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
                  {item.iou === 0 ? "Not learned" : item.iou >= 0.7 ? "Strong" : "Partial"}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="model-detail__side">
          <div className="confusion-panel">
            <h2>Confusion matrix</h2>
            <p>Rows are ground truth; columns are predictions.</p>
            <Matrix
              values={unet.confusion_matrix}
              labels={unet.per_class.map((item) => shortLabel(item.name))}
              titles={unet.per_class.map((item) => item.name)}
              caption="Test-split confusion matrix"
              rowAxis="Truth"
              columnAxis="Predicted"
              describe={(truth, predicted, value) =>
                `${truth} predicted as ${predicted}: ${value.toLocaleString("en")} pixels`
              }
            />
            <p className="analysis-note">
              The two empty columns are the classes the model never predicts, so no pixel can land in them.
            </p>
          </div>
          <section className="method-note">
            <h2>What the aggregate hides</h2>
            <p>Tree cover and permanent water dominate useful performance. Exposed terrain and herbaceous wetland score zero because the source data contributes too few pixels for this four-epoch CPU run. The application keeps those classes visible so a polished demo cannot erase the model’s blind spots.</p>
          </section>
        </div>
      </section>
    </article>
  );
}

function ModelSummary({ name, metrics, selected = false }: { name: string; metrics: MetricSet; selected?: boolean }) {
  return (
    <div className="model-summary" data-selected={selected}>
      <div><span>{name}</span>{selected && <small>Runtime model</small>}</div>
      <dl>
        <div><dt>mIoU</dt><dd>{formatMetric(metrics.mean_iou)}</dd></div>
        <div><dt>Macro Dice</dt><dd>{formatMetric(metrics.mean_dice)}</dd></div>
        <div><dt>Pixel accuracy</dt><dd>{formatMetric(metrics.pixel_accuracy)}</dd></div>
        <div><dt>ECE</dt><dd>{metrics.expected_calibration_error === null ? "—" : formatMetric(metrics.expected_calibration_error)}</dd></div>
      </dl>
    </div>
  );
}

/** "Herbaceous wetland" has to fit a matrix column two characters wide. */
function shortLabel(name: string): string {
  const overrides: Record<string, string> = {
    "Tree cover": "Trees",
    "Low vegetation": "Low veg.",
    "Exposed terrain": "Terrain",
    "Permanent water": "Water",
    "Herbaceous wetland": "Wetland",
  };
  return overrides[name] ?? name;
}

function formatMetric(value: number): string {
  return value.toFixed(3);
}
