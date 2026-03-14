import { useEffect, useState } from "react";
import { motion } from "framer-motion";

export default function AuthPanel({
  apiKey,
  authUser,
  isAuthenticating,
  onConnect,
  onDisconnect,
  authError,
}) {
  const [draftKey, setDraftKey] = useState(apiKey);

  useEffect(() => {
    setDraftKey(apiKey);
  }, [apiKey]);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05, duration: 0.45 }}
      className="glass-panel rounded-[28px] p-6 sm:p-7"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="section-title text-xl font-semibold text-white">Access Control</p>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-300">
            Workspace actions are protected by bearer API keys. Jobs and runs are owned per
            authenticated analyst account.
          </p>
        </div>
        <div className="status-pill">{authUser ? `Signed in as ${authUser.user_id}` : "Authentication Required"}</div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-[1fr_auto_auto]">
        <input
          type="password"
          value={draftKey}
          onChange={(event) => setDraftKey(event.target.value)}
          placeholder="Enter bearer API key"
          className="field-select"
          autoComplete="off"
        />
        <button
          type="button"
          className="action-button"
          onClick={() => onConnect(draftKey)}
          disabled={isAuthenticating || !draftKey.trim()}
        >
          {isAuthenticating ? "Connecting..." : "Connect"}
        </button>
        <button
          type="button"
          className="subtle-button"
          onClick={() => {
            setDraftKey("");
            onDisconnect();
          }}
          disabled={isAuthenticating && !authUser}
        >
          Sign Out
        </button>
      </div>

      {authError ? (
        <div className="mt-4 rounded-2xl border border-rose-300/15 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
          {authError}
        </div>
      ) : authUser ? (
        <div className="mt-4 rounded-2xl border border-emerald-300/15 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
          Authenticated ownership scope: <span className="font-semibold">{authUser.user_id}</span>
        </div>
      ) : null}
    </motion.section>
  );
}
