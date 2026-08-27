import { ExternalLink, Github, Satellite } from "lucide-react";

export function About() {
  return (
    <article className="about-page">
      <header>
        <Satellite aria-hidden="true" />
        <h1>Predictions first. Claims second.</h1>
        <p>RasterScope is a local semantic-segmentation workbench built to make model behavior inspectable, including the parts that do not work.</p>
      </header>
      <div className="about-grid">
        <section>
          <h2>Pipeline</h2>
          <ol>
            <li>Pin and audit 790 Sentinel-2 / WorldCover tiles.</li>
            <li>Create a deterministic 70/15/15 split.</li>
            <li>Compare an RGB centroid baseline with a compact U-Net.</li>
            <li>Export the best checkpoint to ONNX and verify parity.</li>
            <li>Compute areas and transitions with deterministic code.</li>
          </ol>
        </section>
        <section>
          <h2>Boundaries</h2>
          <p>The model uses RGB alone, trains on Norway-focused tiles, and cannot infer why a transition occurred. Outputs are screening evidence, not cadastral, ecological, or legal conclusions.</p>
        </section>
      </div>
      <footer className="about-footer">
        <a href="https://github.com/diegormirhan" target="_blank" rel="noreferrer"><Github aria-hidden="true" />Diego Mirhan on GitHub<ExternalLink aria-hidden="true" /></a>
        <a href="https://huggingface.co/datasets/nikolkoo/SatelliteSegmentation" target="_blank" rel="noreferrer">Dataset card<ExternalLink aria-hidden="true" /></a>
      </footer>
    </article>
  );
}

