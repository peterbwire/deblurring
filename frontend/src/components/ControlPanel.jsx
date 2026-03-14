import { motion } from "framer-motion";

const denoiseOptions = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const deblurOptions = [
  { value: "mild", label: "Mild" },
  { value: "standard", label: "Standard" },
  { value: "aggressive", label: "Aggressive" },
];

const upscaleOptions = [
  { value: "none", label: "None" },
  { value: "2x", label: "2x" },
];

const statusStyles = {
  neutral: "text-slate-300",
  progress: "text-cyan-100",
  ready: "text-emerald-100",
  complete: "text-emerald-100",
  error: "text-rose-100",
};

function ToggleRow({ label, description, checked, onChange }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-white/6 bg-slate-950/35 px-4 py-3">
      <div className="pr-4">
        <div className="text-sm font-medium text-white">{label}</div>
        <div className="mt-1 text-xs leading-5 text-slate-400">{description}</div>
      </div>

      <button
        type="button"
        className="shrink-0"
        onClick={() => onChange(!checked)}
        aria-pressed={checked}
      >
        <span className="toggle-track" data-state={checked ? "on" : "off"}>
          <span
            className="toggle-thumb"
            style={{ transform: checked ? "translateX(1.45rem)" : "translateX(0.25rem)" }}
          />
        </span>
      </button>
    </div>
  );
}

export default function ControlPanel({
  settings,
  onSettingChange,
  onProcess,
  onDownloadImage,
  onDownloadLog,
  isBusy,
  canProcess,
  hasResult,
  selectedFileName,
  jobId,
  runId,
  status,
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1, duration: 0.45 }}
      className="glass-panel rounded-[28px] p-6 sm:p-7"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="section-title text-xl font-semibold text-white">Restoration Controls</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Choose conservative classical enhancement settings and run a traceable restoration job.
          </p>
        </div>
        <div className="status-pill">
          {runId ? `Run ${runId}` : jobId ? `Job ${jobId}` : "No Job Yet"}
        </div>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <label>
          <span className="field-label">Denoise Strength</span>
          <select
            className="field-select"
            value={settings.denoise_strength}
            onChange={(event) => onSettingChange("denoise_strength", event.target.value)}
          >
            {denoiseOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="field-label">Deblur Mode</span>
          <select
            className="field-select"
            value={settings.deblur_mode}
            onChange={(event) => onSettingChange("deblur_mode", event.target.value)}
          >
            {deblurOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="md:col-span-2">
          <span className="field-label">Upscale</span>
          <select
            className="field-select"
            value={settings.upscale}
            onChange={(event) => onSettingChange("upscale", event.target.value)}
          >
            {upscaleOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-5 space-y-3">
        <ToggleRow
          label="Sharpen edges"
          description="Adds edge-aware sharpening after the base deblur pass."
          checked={settings.sharpen_edges}
          onChange={(value) => onSettingChange("sharpen_edges", value)}
        />
        <ToggleRow
          label="Evidence-safe mode"
          description="Limits aggressive settings and skips riskier enhancement steps."
          checked={settings.evidence_safe}
          onChange={(value) => onSettingChange("evidence_safe", value)}
        />
      </div>

      <div className="mt-6 rounded-3xl border border-cyan-200/10 bg-slate-950/35 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
          Processing Status
        </div>
        <p className={`mt-3 text-sm leading-6 ${statusStyles[status.type] || statusStyles.neutral}`}>
          {status.text}
        </p>
        {selectedFileName ? (
          <p className="mt-2 text-xs text-slate-500">Current source: {selectedFileName}</p>
        ) : null}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <button type="button" className="action-button" onClick={onProcess} disabled={!canProcess || isBusy}>
          {isBusy ? "Processing..." : "Process Image"}
        </button>
        <button
          type="button"
          className="subtle-button"
          onClick={onDownloadImage}
          disabled={!hasResult}
        >
          Download Restored Image
        </button>
        <button
          type="button"
          className="subtle-button sm:col-span-2"
          onClick={onDownloadLog}
          disabled={!hasResult}
        >
          Download Audit Log
        </button>
      </div>
    </motion.section>
  );
}
