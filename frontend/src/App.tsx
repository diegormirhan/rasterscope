import { useCallback, useEffect, useState } from "react";

import { fetchModels, fetchScenarios } from "./api";
import { About } from "./components/About";
import { AnalysisRail } from "./components/AnalysisRail";
import { CompareStage } from "./components/CompareStage";
import { ModelLab } from "./components/ModelLab";
import { SideNav } from "./components/SideNav";
import { Toolbar } from "./components/Toolbar";
import { UploadDialog } from "./components/UploadDialog";
import type { Layer, ModelCatalog, Scenario, ScenarioCatalog, Surface } from "./types";

export function App() {
  const [surface, setSurface] = useState<Surface>("compare");
  const [catalog, setCatalog] = useState<ScenarioCatalog | null>(null);
  const [models, setModels] = useState<ModelCatalog | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [layer, setLayer] = useState<Layer>("image");
  const [opacity, setOpacity] = useState(0.56);
  const [isUploadOpen, setUploadOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchScenarios(), fetchModels()])
      .then(([scenarioCatalog, modelCatalog]) => {
        if (!active) return;
        setCatalog(scenarioCatalog);
        setModels(modelCatalog);
        setSelectedScenario((current) => current ?? scenarioCatalog.scenarios[0] ?? null);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "RasterScope could not load.");
      });
    return () => {
      active = false;
    };
  }, [retryKey]);

  const handleUploadComplete = useCallback((scenario: Scenario) => {
    setCatalog((current) =>
      current
        ? { ...current, scenarios: [scenario, ...current.scenarios.filter((item) => item.id !== scenario.id)] }
        : { generated_at: scenario.before.datetime ?? "", model: "unet.onnx", scenarios: [scenario] },
    );
    setSelectedScenario(scenario);
    setLayer("mask");
    setUploadOpen(false);
    setSurface("compare");
  }, []);

  return (
    <div className="app-shell">
      <SideNav activeSurface={surface} onSurfaceChange={setSurface} />
      <main className="app-main" id="main-content">
        {surface === "compare" && (
          <>
            <Toolbar
              catalog={catalog}
              selectedScenario={selectedScenario}
              layer={layer}
              opacity={opacity}
              onScenarioChange={setSelectedScenario}
              onLayerChange={setLayer}
              onOpacityChange={setOpacity}
              onUpload={() => setUploadOpen(true)}
            />
            {error ? (
              <section className="error-state" role="alert">
                <h1>The workbench did not load.</h1>
                <p>{error} Start the FastAPI service, then retry.</p>
                <button className="button button--primary" onClick={() => setRetryKey((key) => key + 1)}>
                  Retry loading
                </button>
              </section>
            ) : selectedScenario ? (
              <div className="compare-workspace">
                <CompareStage scenario={selectedScenario} layer={layer} opacity={opacity} />
                <AnalysisRail scenario={selectedScenario} />
              </div>
            ) : (
              <LoadingWorkbench />
            )}
          </>
        )}
        {surface === "model-lab" && <ModelLab models={models} isLoading={!models && !error} />}
        {surface === "about" && <About />}
      </main>
      <UploadDialog
        open={isUploadOpen}
        onClose={() => setUploadOpen(false)}
        onComplete={handleUploadComplete}
      />
    </div>
  );
}

function LoadingWorkbench() {
  return (
    <div className="workbench-skeleton" aria-label="Loading comparison workbench" aria-busy="true">
      <div className="skeleton skeleton--image" />
      <div className="skeleton-stack">
        <div className="skeleton skeleton--line" />
        <div className="skeleton skeleton--block" />
        <div className="skeleton skeleton--block" />
      </div>
    </div>
  );
}

