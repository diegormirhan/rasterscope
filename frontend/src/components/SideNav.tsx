import { FlaskConical, Info, Layers3, ScanSearch } from "lucide-react";

import type { Surface } from "../types";

interface SideNavProps {
  activeSurface: Surface;
  onSurfaceChange: (surface: Surface) => void;
}

const destinations: Array<{ id: Surface; label: string; icon: typeof Layers3 }> = [
  { id: "compare", label: "Compare", icon: Layers3 },
  { id: "model-lab", label: "Model lab", icon: FlaskConical },
  { id: "about", label: "About", icon: Info },
];

export function SideNav({ activeSurface, onSurfaceChange }: SideNavProps) {
  return (
    <nav className="side-nav" aria-label="Primary navigation">
      <button className="brand" onClick={() => onSurfaceChange("compare")} aria-label="Open RasterScope compare">
        <ScanSearch aria-hidden="true" />
        <span>RasterScope</span>
      </button>
      <div className="side-nav__links">
        {destinations.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className="nav-item"
            data-active={activeSurface === id}
            aria-current={activeSurface === id ? "page" : undefined}
            onClick={() => onSurfaceChange(id)}
          >
            <Icon aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </div>
      <p className="side-nav__runtime">Local runtime</p>
    </nav>
  );
}

