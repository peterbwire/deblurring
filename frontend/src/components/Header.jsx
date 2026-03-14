import { motion } from "framer-motion";

const statusMap = {
  online: {
    label: "Backend Online",
    tone: "bg-emerald-400",
    detail: "API ready for upload and processing.",
  },
  offline: {
    label: "Backend Unreachable",
    tone: "bg-rose-400",
    detail: "Start FastAPI locally to enable processing.",
  },
  checking: {
    label: "Checking Backend",
    tone: "bg-amber-300",
    detail: "Confirming local API availability.",
  },
};

const getQueueState = (opsMetrics) => {
  if (!opsMetrics) {
    return {
      label: "Queue Visibility Locked",
      tone: "bg-slate-400",
      detail: "Authenticate to inspect worker capacity and live queue depth.",
    };
  }

  if (opsMetrics.queued_runs >= opsMetrics.queue_max_size) {
    return {
      label: "Queue Saturated",
      tone: "bg-rose-400",
      detail: "New processing requests may be rejected until worker capacity frees up.",
    };
  }

  if (opsMetrics.queued_runs > 0 || opsMetrics.active_runs > 0) {
    return {
      label: "Queue Active",
      tone: "bg-amber-300",
      detail: "Workers are currently processing or holding queued restoration runs.",
    };
  }

  return {
    label: "Queue Healthy",
    tone: "bg-emerald-400",
    detail: "Workers are available and the processing queue is clear.",
  };
};

export default function Header({ backendStatus, opsMetrics }) {
  const status = statusMap[backendStatus] || statusMap.checking;
  const queueState = getQueueState(opsMetrics);

  return (
    <header className="relative overflow-hidden border-b border-white/5">
      <div className="mx-auto max-w-7xl px-6 pb-10 pt-8 lg:px-10 lg:pb-14 lg:pt-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between"
        >
          <div className="max-w-3xl">
            <div className="status-pill">
              <span className={`h-2.5 w-2.5 rounded-full ${status.tone}`} />
              Lawful forensic enhancement workspace
            </div>
            <h1 className="section-title mt-6 text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              ForensiClear
            </h1>
            <p className="mt-3 text-lg text-cyan-100/90 sm:text-xl">
              Restore clarity. Preserve integrity.
            </p>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
              A forensic-style restoration workspace for lawful image enhancement, deblurring,
              denoising, and audit-safe export. Originals stay preserved, every processing step is
              logged, and outputs are framed with evidentiary caution.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:max-w-xl">
            <div className="glass-panel rounded-3xl p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                System State
              </div>
              <div className="mt-3 flex items-center gap-3">
                <span className={`h-3 w-3 rounded-full ${status.tone}`} />
                <span className="text-base font-semibold text-white">{status.label}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{status.detail}</p>
            </div>

            <div className="glass-panel rounded-3xl p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                Operations Queue
              </div>
              <div className="mt-3 flex items-center gap-3">
                <span className={`h-3 w-3 rounded-full ${queueState.tone}`} />
                <span className="text-base font-semibold text-white">{queueState.label}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{queueState.detail}</p>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-300">
                <div className="rounded-2xl border border-white/6 bg-slate-950/35 px-3 py-3">
                  <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                    Workers
                  </div>
                  <div className="mt-2 text-lg font-semibold text-white">
                    {opsMetrics?.worker_count ?? "--"}
                  </div>
                </div>
                <div className="rounded-2xl border border-white/6 bg-slate-950/35 px-3 py-3">
                  <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                    Active
                  </div>
                  <div className="mt-2 text-lg font-semibold text-white">
                    {opsMetrics?.active_runs ?? "--"}
                  </div>
                </div>
                <div className="rounded-2xl border border-white/6 bg-slate-950/35 px-3 py-3">
                  <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                    Queued
                  </div>
                  <div className="mt-2 text-lg font-semibold text-white">
                    {opsMetrics?.queued_runs ?? "--"}
                  </div>
                </div>
                <div className="rounded-2xl border border-white/6 bg-slate-950/35 px-3 py-3">
                  <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                    Capacity
                  </div>
                  <div className="mt-2 text-lg font-semibold text-white">
                    {opsMetrics?.queue_max_size ?? "--"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </header>
  );
}
