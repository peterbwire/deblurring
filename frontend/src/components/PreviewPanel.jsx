import { useMemo, useState } from "react";
import { motion } from "framer-motion";

export default function PreviewPanel({
  originalUrl,
  restoredUrl,
  duration,
  warnings,
  onCopyWarning,
  copyState,
}) {
  const [viewMode, setViewMode] = useState("compare");
  const [sliderValue, setSliderValue] = useState(54);

  const hasImages = Boolean(originalUrl);
  const hasComparison = Boolean(originalUrl && restoredUrl);
  const copyLabel = useMemo(() => {
    if (copyState === "copied") {
      return "Caution Copied";
    }
    if (copyState === "failed") {
      return "Copy Unavailable";
    }
    return "Copy Caution Note";
  }, [copyState]);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.45 }}
      className="glass-panel rounded-[28px] p-6 sm:p-7"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="section-title text-xl font-semibold text-white">Before / After Review</p>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
            Compare the preserved source and enhanced output side by side or with an interactive
            split slider. Always reference the original alongside the restoration.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={`subtle-button ${viewMode === "compare" ? "border-cyan-300/35 bg-cyan-300/10" : ""}`}
            onClick={() => setViewMode("compare")}
            disabled={!hasComparison}
          >
            Split View
          </button>
          <button
            type="button"
            className={`subtle-button ${viewMode === "side-by-side" ? "border-cyan-300/35 bg-cyan-300/10" : ""}`}
            onClick={() => setViewMode("side-by-side")}
            disabled={!hasComparison}
          >
            Side by Side
          </button>
        </div>
      </div>

      {hasImages ? (
        <div className="mt-6">
          {hasComparison && viewMode === "compare" ? (
            <div>
              <div className="relative aspect-[16/10] overflow-hidden rounded-[26px] border border-white/8 bg-slate-950/70">
                <img
                  src={originalUrl}
                  alt="Original upload"
                  className="absolute inset-0 h-full w-full object-contain"
                />
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ clipPath: `inset(0 ${100 - sliderValue}% 0 0)` }}
                >
                  <img
                    src={restoredUrl}
                    alt="Restored output"
                    className="absolute inset-0 h-full w-full object-contain"
                  />
                </div>
                <div
                  className="absolute inset-y-0 w-px bg-cyan-200"
                  style={{ left: `${sliderValue}%` }}
                />
                <div className="absolute left-4 top-4 rounded-full bg-slate-950/75 px-3 py-1 text-xs font-medium text-slate-100">
                  Original
                </div>
                <div className="absolute right-4 top-4 rounded-full bg-cyan-300/15 px-3 py-1 text-xs font-medium text-cyan-50">
                  Enhanced
                </div>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={sliderValue}
                onChange={(event) => setSliderValue(Number(event.target.value))}
                className="mt-4 h-2 w-full cursor-pointer accent-cyan-300"
              />
            </div>
          ) : hasComparison ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-[26px] border border-white/8 bg-slate-950/65 p-4">
                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Original Upload
                </div>
                <div className="aspect-[4/3] overflow-hidden rounded-3xl bg-slate-950/80">
                  <img src={originalUrl} alt="Original upload" className="h-full w-full object-contain" />
                </div>
              </div>
              <div className="rounded-[26px] border border-cyan-300/10 bg-slate-950/65 p-4">
                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Restored Output
                </div>
                <div className="aspect-[4/3] overflow-hidden rounded-3xl bg-slate-950/80">
                  <img src={restoredUrl} alt="Restored output" className="h-full w-full object-contain" />
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-[26px] border border-white/8 bg-slate-950/65 p-4">
              <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Original Upload
              </div>
              <div className="aspect-[4/3] overflow-hidden rounded-3xl bg-slate-950/80">
                <img src={originalUrl} alt="Original upload" className="h-full w-full object-contain" />
              </div>
            </div>
          )}

          <div className="mt-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2">
              <span className="status-pill">Original preserved</span>
              {duration ? <span className="status-pill">{duration.toFixed(3)}s runtime</span> : null}
            </div>
            <button type="button" className="subtle-button" onClick={onCopyWarning}>
              {copyLabel}
            </button>
          </div>

          {warnings?.length ? (
            <div className="mt-5 flex flex-wrap gap-2">
              {warnings.map((warning) => (
                <span key={warning} className="warning-pill">
                  {warning}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="mt-6 rounded-[26px] border border-white/8 bg-slate-950/50 px-6 py-14 text-center text-sm text-slate-400">
          Upload a supported image to begin your forensic-style review workspace.
        </div>
      )}
    </motion.section>
  );
}
