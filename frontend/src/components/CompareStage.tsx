import { LocateFixed } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

import { inspectPixel } from "../api";
import { spring, type SpringHandle } from "../lib/spring";
import type { Layer, Phase, PixelInspection, Scenario } from "../types";

interface CompareStageProps {
  scenario: Scenario;
  layer: Layer;
  opacity: number;
}

const READOUT_MARGIN = 8;

const clampPercent = (value: number) => Math.max(0, Math.min(100, value));

export function CompareStage({ scenario, layer, opacity }: CompareStageProps) {
  const [position, setPosition] = useState(50);
  const [inspection, setInspection] = useState<PixelInspection | null>(null);
  const [inspectionError, setInspectionError] = useState<string | null>(null);
  const [isDragging, setDragging] = useState(false);

  const stageRef = useRef<HTMLDivElement>(null);
  const readoutRef = useRef<HTMLDivElement>(null);
  const positionRef = useRef(50);
  const grabOffsetRef = useRef(0);
  const springRef = useRef<SpringHandle | null>(null);

  /* The divider writes straight to the DOM so it tracks the pointer within the
   * same frame as the input. React state follows for assistive technology and
   * for deciding which phase a click lands on. */
  const applyPosition = useCallback((next: number) => {
    const clamped = clampPercent(next);
    positionRef.current = clamped;
    stageRef.current?.style.setProperty("--divider", `${clamped}%`);
    setPosition(clamped);
  }, []);

  const cancelSpring = useCallback(() => {
    const running = springRef.current;
    springRef.current = null;
    return running?.stop() ?? null;
  }, []);

  useEffect(() => {
    return () => {
      cancelSpring();
    };
  }, [cancelSpring]);

  // A new scenario is a new measurement; nothing from the previous one carries over.
  useEffect(() => {
    setInspection(null);
    setInspectionError(null);
  }, [scenario.id]);

  useEffect(() => {
    if (!inspection) return;
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") setInspection(null);
    };
    window.addEventListener("keydown", dismiss);
    return () => window.removeEventListener("keydown", dismiss);
  }, [inspection]);

  /* Keep the readout inside the frame. Anchoring it on the pixel alone pushes it
   * out of view near any edge, where it is then clipped by the frame. */
  useLayoutEffect(() => {
    const readout = readoutRef.current;
    const stage = stageRef.current;
    if (!readout || !stage || !inspection) return;
    const frame = stage.getBoundingClientRect();
    const anchorX = (inspection.x / 256) * frame.width;
    const anchorY = (inspection.y / 256) * frame.height;
    const half = readout.offsetWidth / 2;
    const above = anchorY - readout.offsetHeight - 14 >= 0;
    readout.style.setProperty(
      "--readout-x",
      `${Math.max(half + READOUT_MARGIN, Math.min(frame.width - half - READOUT_MARGIN, anchorX))}px`,
    );
    readout.style.setProperty("--readout-y", `${anchorY}px`);
    readout.dataset.placement = above ? "above" : "below";
  }, [inspection]);

  const inspect = async (clientX: number, clientY: number) => {
    const bounds = stageRef.current?.getBoundingClientRect();
    if (!bounds) return;
    const ratioX = (clientX - bounds.left) / bounds.width;
    const ratioY = (clientY - bounds.top) / bounds.height;
    const x = Math.max(0, Math.min(255, Math.floor(ratioX * 256)));
    const y = Math.max(0, Math.min(255, Math.floor(ratioY * 256)));
    const phase: Phase = ratioX * 100 <= positionRef.current ? "after" : "before";
    setInspectionError(null);
    try {
      setInspection(await inspectPixel(scenario.id, phase, x, y));
    } catch (reason) {
      setInspection(null);
      setInspectionError(reason instanceof Error ? reason.message : "Pixel inspection failed.");
    }
  };

  const beginDrag = (event: React.PointerEvent<HTMLElement>) => {
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    const bounds = stageRef.current?.getBoundingClientRect();
    // Interrupting a spring hands its live value over instead of snapping.
    const interrupted = cancelSpring();
    if (interrupted) applyPosition(interrupted.value);
    // Respect where the divider was grabbed; never recentre it under the pointer.
    grabOffsetRef.current = bounds
      ? clientToPercent(event.clientX, bounds) - positionRef.current
      : 0;
    setDragging(true);
  };

  const continueDrag = (event: React.PointerEvent<HTMLElement>) => {
    if (!isDragging) return;
    const bounds = stageRef.current?.getBoundingClientRect();
    if (!bounds) return;
    applyPosition(clientToPercent(event.clientX, bounds) - grabOffsetRef.current);
  };

  const endDrag = () => setDragging(false);

  const recentre = () => {
    const start = cancelSpring()?.value ?? positionRef.current;
    springRef.current = spring({
      from: start,
      to: 50,
      response: 0.4,
      onFrame: applyPosition,
      onRest: () => {
        springRef.current = null;
      },
    });
  };

  const nudge = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    const step = event.shiftKey ? 10 : 2;
    const moves: Record<string, number> = {
      ArrowLeft: -step,
      ArrowRight: step,
      ArrowDown: -step,
      ArrowUp: step,
    };
    if (event.key in moves) {
      event.preventDefault();
      cancelSpring();
      applyPosition(positionRef.current + moves[event.key]);
      return;
    }
    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      cancelSpring();
      applyPosition(event.key === "Home" ? 0 : 100);
    }
  };

  return (
    <section className="comparison" aria-label="Satellite image comparison">
      <div className="comparison__heading">
        <div>
          <h1>Land-cover change</h1>
          <p>{scenario.location}</p>
        </div>
        <p className="comparison__hint">
          <LocateFixed aria-hidden="true" /> Select the image to inspect a pixel
        </p>
      </div>
      {scenario.domain_shift && (
        <div className="domain-notice" role="note">
          <strong>Domain shift</strong>
          <span>This geography is outside the Norway-focused training distribution.</span>
        </div>
      )}
      <div className="comparison-stage">
      <div
        className="comparison-frame"
        ref={stageRef}
        data-dragging={isDragging}
        style={{ "--divider": `${position}%` } as React.CSSProperties}
        onClick={(event) => void inspect(event.clientX, event.clientY)}
        onPointerMove={continueDrag}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        <ImageLayer scenario={scenario} phase="before" layer={layer} opacity={opacity} />
        <div className="comparison-frame__after">
          <ImageLayer scenario={scenario} phase="after" layer={layer} opacity={opacity} />
        </div>
        <span className="image-date image-date--after">After · {formatDate(scenario.after.datetime)}</span>
        <span className="image-date image-date--before">Before · {formatDate(scenario.before.datetime)}</span>
        <div
          className="comparison-divider"
          onPointerDown={beginDrag}
          onClick={(event) => event.stopPropagation()}
          aria-hidden="true"
        />
        <button
          type="button"
          className="comparison-handle"
          role="slider"
          aria-label="Comparison divider"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(position)}
          aria-valuetext={`${Math.round(position)}% after image`}
          onClick={(event) => event.stopPropagation()}
          onDoubleClick={recentre}
          onPointerDown={beginDrag}
          onKeyDown={nudge}
        >
          <span className="comparison-handle__grip" aria-hidden="true" />
        </button>
        {inspection && (
          <>
            <span
              className="pixel-marker"
              aria-hidden="true"
              style={
                {
                  insetInlineStart: `${((inspection.x + 0.5) / 256) * 100}%`,
                  insetBlockStart: `${((inspection.y + 0.5) / 256) * 100}%`,
                } as React.CSSProperties
              }
            />
            <div className="pixel-readout" ref={readoutRef} aria-live="polite">
              <span className="pixel-readout__head">
                <span className={`class-swatch class-swatch--${inspection.class_id}`} />
                <strong>{inspection.class_name}</strong>
              </span>
              <span className="pixel-readout__row">
                <span>Confidence</span>
                <b>{Math.round(inspection.confidence * 100)}%</b>
              </span>
              <span className="pixel-readout__row">
                <span>Uncertainty</span>
                <b>{Math.round(inspection.uncertainty * 100)}%</b>
              </span>
              <span className="pixel-readout__meta">
                {inspection.phase} · x {inspection.x} · y {inspection.y}
              </span>
            </div>
          </>
        )}
      </div>
      </div>
      {inspectionError && (
        <p className="inline-error" role="alert">
          {inspectionError} Select another pixel or retry.
        </p>
      )}
      <p className="source-line">
        Sentinel-2 L2A · {scenario.before.item_id} → {scenario.after.item_id}
      </p>
    </section>
  );
}

function clientToPercent(clientX: number, bounds: DOMRect): number {
  return clampPercent(((clientX - bounds.left) / bounds.width) * 100);
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
