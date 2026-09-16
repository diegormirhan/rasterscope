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
          <h2>Where the line sits</h2>
          <p>The network proposes a class for every pixel. Everything after that — pixel counts, hectare conversion, deltas, the transition matrix and the exported report — is deterministic code with its own tests, so a change to the model cannot quietly change an arithmetic result.</p>
        </section>
        <section>
          <h2>Boundaries</h2>
          <p>The model uses RGB alone, trains on Norway-focused tiles, and cannot infer why a transition occurred. Outputs are screening evidence, not cadastral, ecological, or legal conclusions.</p>
        </section>
      </div>
      <footer className="about-footer">
        <a href="https://github.com/diegormirhan/rasterscope" target="_blank" rel="noreferrer"><Github aria-hidden="true" />Source on GitHub<ExternalLink aria-hidden="true" /></a>
        <a href="https://huggingface.co/datasets/nikolkoo/SatelliteSegmentation" target="_blank" rel="noreferrer">Dataset card<ExternalLink aria-hidden="true" /></a>
        <a href="https://diegomirhan.com" target="_blank" rel="noreferrer">Diego Mirhan<ExternalLink aria-hidden="true" /></a>
      </footer>
    </article>
  );
}
