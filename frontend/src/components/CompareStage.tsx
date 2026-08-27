import { GripVertical, LocateFixed } from "lucide-react";
import { useRef, useState } from "react";

import { inspectPixel } from "../api";
import type { Layer, Phase, PixelInspection, Scenario } from "../types";

interface CompareStageProps {
  scenario: Scenario;
  layer: Layer;
  opacity: number;
}

export function CompareStage({ scenario, layer, opacity }: CompareStageProps) {
  const [position, setPosition] = useState(50);
  const [inspection, setInspection] = useState<PixelInspection | null>(null);
  const [inspectionError, setInspectionError] = useState<string | null>(null);
  const [isDragging, setDragging] = useState(false);
  const moved = useRef(false);
  const stageRef = useRef<HTMLDivElement>(null);

  const setPositionFromPointer = (clientX: number) => {
    const bounds = stageRef.current?.getBoundingClientRect();
    if (!bounds) return;
    setPosition(Math.max(0, Math.min(100, ((clientX - bounds.left) / bounds.width) * 100)));
  };

  const handleStageClick = async (clientX: number, clientY: number) => {
    if (moved.current) {
      moved.current = false;
      return;
    }
    const bounds = stageRef.current?.getBoundingClientRect();
    if (!bounds) return;
    const x = Math.max(0, Math.min(255, Math.floor(((clientX - bounds.left) / bounds.width) * 256)));
    const y = Math.max(0, Math.min(255, Math.floor(((clientY - bounds.top) / bounds.height) * 256)));
    const phase: Phase = ((clientX - bounds.left) / bounds.width) * 100 <= position ? "after" : "before";
    setInspectionError(null);
    try {
      setInspection(await inspectPixel(scenario.id, phase, x, y));
    } catch (reason) {
      setInspectionError(reason instanceof Error ? reason.message : "Pixel inspection failed.");
    }
  };

  return (
    <section className="comparison" aria-label="Satellite image comparison">
      <div className="comparison__heading">
        <div>
          <h1>Land-cover change</h1>
          <p>{scenario.location}</p>
        </div>
        <p className="comparison__hint"><LocateFixed aria-hidden="true" /> Select the image to inspect a pixel</p>
      </div>
      {scenario.domain_shift && (
        <div className="domain-notice" role="note">
          <strong>Domain shift</strong>
          <span>This geography is outside the Norway-focused training distribution.</span>
        </div>
      )}
      <div
        className="comparison-frame"
        ref={stageRef}
        onClick={(event) => void handleStageClick(event.clientX, event.clientY)}
        onPointerMove={(event) => {
          if (!isDragging) return;
          moved.current = true;
          setPositionFromPointer(event.clientX);
        }}
        onPointerUp={() => setDragging(false)}
        onPointerCancel={() => setDragging(false)}
      >
        <ImageLayer scenario={scenario} phase="before" layer={layer} opacity={opacity} />
        <div className="comparison-frame__after" style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}>
          <ImageLayer scenario={scenario} phase="after" layer={layer} opacity={opacity} />
        </div>
        <span className="image-date image-date--after">After · {formatDate(scenario.after.datetime)}</span>
        <span className="image-date image-date--before">Before · {formatDate(scenario.before.datetime)}</span>
        <div className="comparison-divider" style={{ insetInlineStart: `${position}%` }} aria-hidden="true" />
        <button
          className="comparison-handle"
          style={{ insetInlineStart: `${position}%` }}
          aria-label={`Comparison divider at ${Math.round(position)} percent`}
          onClick={(event) => event.stopPropagation()}
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture(event.pointerId);
            moved.current = false;
            setDragging(true);
          }}
          onPointerUp={() => setDragging(false)}
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
              event.preventDefault();
              setPosition((current) =>
                Math.max(0, Math.min(100, current + (event.key === "ArrowLeft" ? -2 : 2))),
              );
            }
          }}
        >
          <GripVertical aria-hidden="true" />
        </button>
        {inspection && (
          <div
            className="pixel-readout"
            style={{ insetInlineStart: `${(inspection.x / 256) * 100}%`, insetBlockStart: `${(inspection.y / 256) * 100}%` }}
            aria-live="polite"
          >
            <span className={`class-swatch class-swatch--${inspection.class_id}`} />
            <strong>{inspection.class_name}</strong>
            <span>{Math.round(inspection.confidence * 100)}% confidence</span>
            <span>{Math.round(inspection.uncertainty * 100)}% uncertainty</span>
          </div>
        )}
      </div>
      {inspectionError && <p className="inline-error" role="alert">{inspectionError} Select another pixel or retry.</p>}
      <p className="source-line">
        Sentinel-2 L2A · {scenario.before.item_id} → {scenario.after.item_id}
      </p>
    </section>
  );
}

function ImageLayer({ scenario, phase, layer, opacity }: CompareStageProps & { phase: Phase }) {
  const source = scenario.assets[phase];
  const overlay = layer === "mask" ? scenario.assets[`${phase}_mask`] : scenario.assets[`${phase}_uncertainty`];
  return (
    <div className="image-layer">
      <img src={source} alt={`${phase} Sentinel-2 scene for ${scenario.location}`} width="256" height="256" />
      {layer !== "image" && (
        <img
          className="image-layer__overlay"
          src={overlay}
          alt={`${layer} overlay for the ${phase} scene`}
          width="256"
          height="256"
          style={{ opacity }}
        />
      )}
    </div>
  );
}

function formatDate(value: string | null): string {
  return value
    ? new Intl.DateTimeFormat("en", { year: "numeric", month: "short", day: "2-digit" }).format(new Date(value))
    : "Local image";
}

