import { motion } from "framer-motion";

export default function HistoryPanel({ items }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.18, duration: 0.45 }}
      className="glass-panel rounded-[28px] p-6 sm:p-7"
    >
      <div>
        <p className="section-title text-xl font-semibold text-white">Recent Jobs</p>
        <p className="mt-2 text-sm leading-6 text-slate-300">
          Ownership-scoped history from the backend database, including the latest run status for
          each preserved source image.
        </p>
      </div>

      {items?.length ? (
        <div className="mt-6 space-y-3">
          {items.map((item) => (
            <div
              key={item.job_id}
              className="rounded-2xl border border-white/6 bg-slate-950/35 px-4 py-4"
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="text-sm font-semibold text-white">{item.original_filename}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    {item.width} x {item.height} | Job {item.job_id}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="status-pill">{item.latest_run_status || "No runs yet"}</span>
                  {item.latest_run_id ? <span className="status-pill">Run {item.latest_run_id}</span> : null}
                </div>
              </div>
              <div className="mt-3 text-xs text-slate-500">Uploaded {item.uploaded_at}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-6 rounded-[26px] border border-white/8 bg-slate-950/50 px-6 py-14 text-center text-sm text-slate-400">
          No authenticated job history yet.
        </div>
      )}
    </motion.section>
  );
}
