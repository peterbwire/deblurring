import { motion } from "framer-motion";

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/6 bg-slate-950/35 px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-2 text-sm font-medium text-slate-100">{value}</div>
    </div>
  );
}

export default function LogPanel({ auditLog, onDownloadLog }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.45 }}
      className="glass-panel rounded-[28px] p-6 sm:p-7"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="section-title text-xl font-semibold text-white">Audit Log</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Each restoration run records inputs, settings, steps, warnings, and output dimensions
            for review and export.
          </p>
        </div>

        <button type="button" className="subtle-button" onClick={onDownloadLog} disabled={!auditLog}>
          Export Log JSON
        </button>
      </div>

      {auditLog ? (
        <div className="mt-6 space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Job ID" value={auditLog.job_id} />
            <Metric
              label="Original Size"
              value={`${auditLog.original_dimensions.width} x ${auditLog.original_dimensions.height}`}
            />
            <Metric
              label="Output Size"
              value={`${auditLog.output_dimensions.width} x ${auditLog.output_dimensions.height}`}
            />
            <Metric label="Runtime" value={`${auditLog.runtime_seconds}s`} />
          </div>

          <div className="grid gap-5 xl:grid-cols-[0.92fr_1.08fr]">
            <div className="rounded-[24px] border border-white/6 bg-slate-950/35 p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Applied Settings
              </div>
              <dl className="mt-4 space-y-3 text-sm text-slate-200">
                <div className="flex justify-between gap-4 border-b border-white/6 pb-3">
                  <dt className="text-slate-400">Denoise</dt>
                  <dd>{auditLog.denoise_strength_used}</dd>
                </div>
                <div className="flex justify-between gap-4 border-b border-white/6 pb-3">
                  <dt className="text-slate-400">Deblur</dt>
                  <dd>{auditLog.deblur_mode_used}</dd>
                </div>
                <div className="flex justify-between gap-4 border-b border-white/6 pb-3">
                  <dt className="text-slate-400">Sharpen</dt>
                  <dd>{auditLog.sharpen_enabled ? "Enabled" : "Disabled"}</dd>
                </div>
                <div className="flex justify-between gap-4 border-b border-white/6 pb-3">
                  <dt className="text-slate-400">Upscale</dt>
                  <dd>{auditLog.upscale_setting}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-400">Evidence-safe</dt>
                  <dd>{auditLog.evidence_safe ? "Enabled" : "Disabled"}</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-[24px] border border-white/6 bg-slate-950/35 p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Processing Steps
              </div>
              <div className="mt-4 space-y-3">
                {auditLog.processing_steps_applied.map((step) => (
                  <div
                    key={step}
                    className="rounded-2xl border border-cyan-300/10 bg-cyan-300/5 px-4 py-3 text-sm text-slate-100"
                  >
                    {step}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {auditLog.warnings?.length ? (
            <div className="rounded-[24px] border border-amber-300/10 bg-amber-300/5 p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-100/80">
                Warnings
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {auditLog.warnings.map((warning) => (
                  <span key={warning} className="warning-pill">
                    {warning}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          <div className="rounded-[24px] border border-white/6 bg-slate-950/35 p-5">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              Raw Log Snapshot
            </div>
            <pre className="mt-4 max-h-72 overflow-auto rounded-2xl bg-slate-950/80 p-4 text-xs leading-6 text-slate-300">
              {JSON.stringify(auditLog, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <div className="mt-6 rounded-[26px] border border-white/8 bg-slate-950/50 px-6 py-14 text-center text-sm text-slate-400">
          Run a restoration job to generate a structured audit log and exportable JSON report.
        </div>
      )}
    </motion.section>
  );
}
