import { FileImage, LoaderCircle, X } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";

import { analyzePair } from "../api";
import type { Scenario } from "../types";

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onComplete: (scenario: Scenario) => void;
}

export function UploadDialog({ open, onClose, onComplete }: UploadDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [before, setBefore] = useState<File | null>(null);
  const [after, setAfter] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (open && dialog && !dialog.open) dialog.showModal();
    if (!open && dialog?.open) dialog.close();
  }, [open]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!before || !after) {
      setError("Both images are required. Choose an earlier and a later RGB image.");
      setStatus("error");
      return;
    }
    setStatus("loading");
    setError("");
    try {
      onComplete(await analyzePair(before, after));
      setBefore(null);
      setAfter(null);
      setStatus("idle");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The image pair could not be analyzed. Try valid PNG or JPEG files.");
      setStatus("error");
    }
  };

  return (
    <dialog className="upload-dialog" ref={dialogRef} onClose={onClose} onClick={(event) => {
      if (event.target === dialogRef.current) onClose();
    }}>
      <form method="dialog" onSubmit={(event) => void submit(event)}>
        <div className="dialog-heading">
          <div><h2>Analyze local images</h2><p>RasterScope resizes both inputs to 256 x 256 and reports pixel counts.</p></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close upload dialog"><X aria-hidden="true" /></button>
        </div>
        <FileField id="before-upload" label="Earlier image" file={before} onChange={setBefore} />
        <FileField id="after-upload" label="Later image" file={after} onChange={setAfter} />
        <p className="field-help">PNG or JPEG · maximum 12 MB each · inputs should cover the same aligned area</p>
        {status === "error" && <p className="form-error" role="alert">{error}</p>}
        <div className="dialog-actions">
          <button className="button button--secondary" type="button" onClick={onClose}>Cancel</button>
          <button className="button button--primary" type="submit" disabled={status === "loading"} aria-busy={status === "loading"}>
            {status === "loading" ? <><LoaderCircle className="spinner" aria-hidden="true" />Running local inference…</> : "Analyze pair"}
          </button>
        </div>
      </form>
    </dialog>
  );
}

function FileField({ id, label, file, onChange }: { id: string; label: string; file: File | null; onChange: (file: File | null) => void }) {
  return (
    <div className="file-field">
      <span className="file-field__label">{label}</span>
      <label htmlFor={id} className="file-picker">
        <FileImage aria-hidden="true" />
        <span>{file?.name ?? "Choose image"}</span>
        <input id={id} type="file" accept="image/png,image/jpeg" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
      </label>
    </div>
  );
}

