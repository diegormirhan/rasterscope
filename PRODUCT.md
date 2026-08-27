# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated: React and TypeScript for the interface, FastAPI for the local API, PyTorch for training, ONNX Runtime for inference, and `uv` for a reproducible Python 3.12 environment. The product must not use Streamlit or require cloud services at runtime.

## Users

Inferred from the approved brief: the primary users are recruiters and ML engineers reviewing Diego Mirhan's portfolio through a recorded product demo or a local hands-on session. A secondary user is an analyst who needs to inspect land-cover segmentation and change evidence without writing code.

## Product Purpose

RasterScope turns paired satellite images into an inspectable land-cover change analysis. Success means a reviewer can load a bundled scenario or two uploaded images, understand the predicted classes and uncertainty, compare dates, and export an evidence-rich local report.

## Positioning

The project connects reproducible model development, calibrated semantic segmentation, deterministic change accounting, local ONNX inference, and an audit-oriented interface in one portfolio-ready system. The model proposes pixel classes; deterministic code computes areas, transitions, and report content.

## Operating Context

The main demo is recorded at 1440p on a local machine. Users move between an operational comparison workspace and a model lab, inspect bundled scenarios, adjust overlays, click pixels, and export an HTML report. The repository must remain understandable enough to defend in an ML interview.

## Capabilities and Constraints

- Compare before and after imagery with a draggable divider.
- Display semantic masks, confidence, uncertainty, class areas, and a transition matrix.
- Accept local image uploads and include bundled demo scenarios.
- Expose evaluation metrics, confusion matrix, and representative errors in a Model Lab.
- Train and compare a deterministic pixel baseline, a compact U-Net, and a SegFormer transfer-learning path.
- Use deterministic dataset splits, centralized configuration, structured logs, and pinned data/model revisions.
- Run inference and reporting locally; no API key or hosted model is required.
- Use the `nikolkoo/SatelliteSegmentation` dataset under CC BY 4.0 and document its label provenance from ESA WorldCover.
- Treat area values as estimates based on the stated 10 m ground sampling distance.
- Do not imply causal conclusions, cadastral precision, or real-time monitoring.

## Brand Commitments

The name is RasterScope. The voice is technical, direct, and honest. The application should feel like a cartographic analysis instrument, not a generic analytics dashboard. Runtime UI copy and public documentation are in English; the LinkedIn launch post is in Brazilian Portuguese.

## Evidence on Hand

- Approved product concept and feature list from the current task.
- Public source dataset card and upstream Sentinel-2 / ESA WorldCover documentation.
- Real evaluation metrics and screenshots will be generated during implementation; no performance claim exists before training.
- Diego's portfolio and project history establish a preference for local, auditable AI systems.

## Product Principles

1. Show evidence, not confidence theater.
2. Keep learned predictions separate from deterministic measurements.
3. Make every pipeline stage reproducible and inspectable.
4. Prefer a focused local workflow over cloud dependencies.
5. Optimize the product demo for comprehension in under three minutes.

## Accessibility & Inclusion

Target WCAG 2.2 AA for keyboard navigation, focus visibility, semantic labeling, contrast, reduced motion, and color-independent legends.
