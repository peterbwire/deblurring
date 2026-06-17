import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import AuthPanel from "../components/AuthPanel";
import ControlPanel from "../components/ControlPanel";
import Footer from "../components/Footer";
import Header from "../components/Header";
import HistoryPanel from "../components/HistoryPanel";
import LogPanel from "../components/LogPanel";
import PreviewPanel from "../components/PreviewPanel";
import UploadZone from "../components/UploadZone";
import {
  absoluteUrl,
  extractErrorMessage,
  getCurrentUser,
  getOpsMetrics,
  getProcessStatus,
  getRecentJobs,
  getStoredApiKey,
  healthCheck,
  setApiKey,
  startProcess,
  uploadImage,
} from "../services/api";

const defaultSettings = {
  denoise_strength: "medium",
  deblur_mode: "standard",
  sharpen_edges: true,
  deblur_iterations: 18,
  psf_sigma: 1.5,
  upscale: "none",
  use_supervised_model: false,
  evidence_safe: true,
};

const cautionNote =
  "Enhanced outputs improve visibility but may not represent exact lost detail. Always preserve and review the original.";

const progressPhaseCopy = {
  queued: "waiting for an available worker slot.",
  inspecting_original: "inspecting the preserved source image.",
  loading_original: "loading normalized image data for restoration.",
  denoising: "reducing visible sensor and compression noise.",
  deblurring: "applying conservative sharpening and blur recovery.",
  contrast_balancing: "balancing luminance contrast for readability.",
  upscaling: "upscaling for closer inspection without claiming new detail.",
  writing_artifacts: "writing the restored output and audit record.",
  completed: "completed successfully.",
  failed: "failed during processing.",
};

export default function Home() {
  const [settings, setSettings] = useState(defaultSettings);
  const [backendStatus, setBackendStatus] = useState("checking");
  const [apiKey, setApiKeyState] = useState(getStoredApiKey());
  const [authUser, setAuthUser] = useState(null);
  const [authError, setAuthError] = useState("");
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [opsMetrics, setOpsMetrics] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobId, setJobId] = useState("");
  const [runId, setRunId] = useState("");
  const [runState, setRunState] = useState("idle");
  const [originalUrl, setOriginalUrl] = useState("");
  const [restoredUrl, setRestoredUrl] = useState("");
  const [auditLog, setAuditLog] = useState(null);
  const [previousRestoredUrl, setPreviousRestoredUrl] = useState("");
  const [warnings, setWarnings] = useState([]);
  const [duration, setDuration] = useState(null);
  const [logUrl, setLogUrl] = useState("");
  const [imageDownloadUrl, setImageDownloadUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [copyState, setCopyState] = useState("idle");
  const [status, setStatus] = useState({
    type: "neutral",
    text: "Authenticate with a bearer API key to begin a logged restoration job.",
  });

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await healthCheck();
        setBackendStatus("online");
      } catch {
        setBackendStatus("offline");
      }
    };

    checkBackend();
  }, []);

  const refreshJobHistory = async () => {
    try {
      const history = await getRecentJobs();
      setJobHistory(history.items || []);
    } catch {
      setJobHistory([]);
    }
  };

  const refreshOpsMetrics = async () => {
    try {
      const metrics = await getOpsMetrics();
      setOpsMetrics(metrics);
    } catch {
      setOpsMetrics(null);
    }
  };

  const connectWorkspace = async (nextApiKey) => {
    setIsAuthenticating(true);
    setAuthError("");
    try {
      setApiKey(nextApiKey);
      setApiKeyState(nextApiKey.trim());
      const user = await getCurrentUser();
      setAuthUser(user);
      await Promise.all([refreshJobHistory(), refreshOpsMetrics()]);
      setStatus((current) =>
        current.type === "neutral" || current.text.includes("Authenticate")
          ? {
              type: "ready",
              text: "Authentication successful. Upload an image to begin a logged restoration job.",
            }
          : current,
      );
    } catch (error) {
      setApiKey("");
      setApiKeyState("");
      setAuthUser(null);
      setOpsMetrics(null);
      setJobHistory([]);
      setAuthError(extractErrorMessage(error));
      setStatus({
        type: "error",
        text: "Authentication failed. Enter a valid bearer API key to continue.",
      });
    } finally {
      setIsAuthenticating(false);
    }
  };

  const disconnectWorkspace = () => {
    setApiKey("");
    setApiKeyState("");
    setAuthUser(null);
    setOpsMetrics(null);
    setAuthError("");
    setJobHistory([]);
    setSelectedFile(null);
    setJobId("");
    setRunId("");
    setRunState("idle");
    setOriginalUrl("");
    setErrorMessage("");
    resetProcessedArtifacts();
    setStatus({
      type: "neutral",
      text: "Authenticate with a bearer API key to begin a logged restoration job.",
    });
  };

  useEffect(() => {
    if (!apiKey) {
      return;
    }
    connectWorkspace(apiKey);
  }, []);

  useEffect(() => {
    if (!authUser) {
      setOpsMetrics(null);
      return undefined;
    }

    refreshOpsMetrics();
    const intervalId = window.setInterval(refreshOpsMetrics, 5000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [authUser]);

  const resetProcessedArtifacts = () => {
    setRestoredUrl("");
    setAuditLog(null);
    setWarnings([]);
    setDuration(null);
    setLogUrl("");
    setImageDownloadUrl("");
  };

  const handleSettingChange = (key, value) => {
    setSettings((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleFileAccepted = async (file) => {
    setSelectedFile(file);
    setJobId("");
    setRunId("");
    setRunState("idle");
    setOriginalUrl("");
    setErrorMessage("");
    resetProcessedArtifacts();
    setStatus({
      type: "progress",
      text: "Uploading original source file and creating a preservation-safe job record...",
    });
    setIsUploading(true);

    try {
      const response = await uploadImage(file);
      setJobId(response.job_id);
      setOriginalUrl(absoluteUrl(response.original_url));
      await refreshJobHistory();
      setStatus({
        type: "ready",
        text: "Original preserved successfully. Review settings and process when ready.",
      });
    } catch (error) {
      setSelectedFile(null);
      setErrorMessage(extractErrorMessage(error));
      setStatus({
        type: "error",
        text: "Upload failed. Please review the file format or size and try again.",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcess = async () => {
    if (!jobId) {
      return;
    }

    setIsProcessing(true);
    setErrorMessage("");
    resetProcessedArtifacts();
    setStatus({
      type: "progress",
      text: "Submitting a new immutable processing run...",
    });

    try {
      const response = await startProcess(jobId, settings);
      setRunId(response.run_id);
      setRunState(response.status);
      await refreshOpsMetrics();
      setStatus({
        type: "progress",
        text: `Run ${response.run_id} queued. Processing will begin shortly.`,
      });
    } catch (error) {
      setErrorMessage(extractErrorMessage(error));
      setRunId("");
      setRunState("failed");
      setStatus({
        type: "error",
        text: "Unable to start processing. Please retry or adjust the current settings.",
      });
      setIsProcessing(false);
    }
  };

  useEffect(() => {
    if (!jobId || !runId || !["queued", "processing"].includes(runState)) {
      return undefined;
    }

    let isCancelled = false;

    const pollStatus = async () => {
      try {
        const response = await getProcessStatus(jobId, runId);
        if (isCancelled) {
          return;
        }

        setRunState(response.status);

        if (response.original_url) {
          setOriginalUrl(absoluteUrl(response.original_url));
        }

        if (response.status === "queued") {
          setStatus({
            type: "progress",
            text: `Run ${runId} is ${progressPhaseCopy[response.progress_phase] || "waiting in the processing queue."}`,
          });
          return;
        }

        if (response.status === "processing") {
          const phaseText =
            progressPhaseCopy[response.progress_phase] || "processing the current restoration run.";
          setStatus({
            type: "progress",
            text: `Run ${runId} is ${phaseText}`,
          });
          return;
        }

        if (response.status === "completed") {
          setRestoredUrl(absoluteUrl(response.restored_url));
          setWarnings(response.warnings || []);
          setAuditLog(response.audit_log);
          // if a comparison with previous run exists, fetch its signed restored_url
          const prevName = response.audit_log?.comparison_with_previous?.previous_run;
          if (prevName) {
            try {
              getProcessStatus(jobId, prevName).then((prevResp) => {
                setPreviousRestoredUrl(absoluteUrl(prevResp.restored_url));
              });
            } catch {
              setPreviousRestoredUrl("");
            }
          } else {
            setPreviousRestoredUrl("");
          }
          setDuration(response.duration_seconds);
          setLogUrl(response.log_url);
          setImageDownloadUrl(response.image_download_url);
          setErrorMessage("");
          await Promise.all([refreshJobHistory(), refreshOpsMetrics()]);
          setStatus({
            type: "complete",
            text: `Run ${runId} completed. Compare the output against the preserved original and export what you need.`,
          });
          setIsProcessing(false);
          return;
        }

        setWarnings(response.warnings || []);
        setErrorMessage(response.error_message || "Processing failed.");
        setStatus({
          type: "error",
          text: `Run ${runId} failed. Review the message and try a new run if needed.`,
        });
        refreshOpsMetrics();
        setIsProcessing(false);
      } catch (error) {
        if (isCancelled) {
          return;
        }

        setRunState("failed");
        setErrorMessage(extractErrorMessage(error));
        setStatus({
          type: "error",
          text: "Unable to retrieve the current run status from the backend.",
        });
        refreshOpsMetrics();
        setIsProcessing(false);
      }
    };

    pollStatus();
    const intervalId = window.setInterval(pollStatus, 1500);

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, [jobId, runId, runState]);

  const openUrl = (url) => {
    if (!url) {
      return;
    }
    window.open(absoluteUrl(url), "_blank", "noopener,noreferrer");
  };

  const handleCopyWarning = async () => {
    try {
      await navigator.clipboard.writeText(cautionNote);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }

    window.setTimeout(() => {
      setCopyState("idle");
    }, 1800);
  };

  const selectedFileName = selectedFile?.name || auditLog?.original_filename || "";
  const isLocked = !authUser;
  const isBusy = isUploading || isProcessing;
  const canProcess = Boolean(jobId) && !isBusy && !isLocked;
  const hasResult = Boolean(restoredUrl && auditLog && runState === "completed");

  return (
    <div className="min-h-screen">
      <Header backendStatus={backendStatus} opsMetrics={opsMetrics} />

      <main className="mx-auto max-w-7xl px-6 pb-16 pt-8 lg:px-10">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.45 }}
          className="mb-6 flex flex-wrap gap-3"
        >
          <span className="status-pill">Evidence-safe philosophy</span>
          <span className="status-pill">Original preserved</span>
          <span className="status-pill">Audit log export</span>
          <span className="status-pill">Classical CV pipeline</span>
        </motion.div>

        <div className="grid gap-6 xl:grid-cols-[1.04fr_0.96fr]">
          <div className="space-y-6">
            <AuthPanel
              apiKey={apiKey}
              authUser={authUser}
              isAuthenticating={isAuthenticating}
              onConnect={connectWorkspace}
              onDisconnect={disconnectWorkspace}
              authError={authError}
            />
            <UploadZone
              onFileAccepted={handleFileAccepted}
              isBusy={isBusy}
              isDisabled={isLocked}
              selectedFileName={selectedFileName}
              errorMessage={errorMessage}
            />
            <PreviewPanel
              originalUrl={originalUrl}
              restoredUrl={restoredUrl}
              previousRestoredUrl={previousRestoredUrl}
              comparisonMetrics={auditLog?.comparison_with_previous}
              duration={duration}
              warnings={warnings}
              onCopyWarning={handleCopyWarning}
              copyState={copyState}
            />
          </div>

          <div className="space-y-6">
            <ControlPanel
              settings={settings}
              onSettingChange={handleSettingChange}
              onProcess={handleProcess}
              onDownloadImage={() => openUrl(imageDownloadUrl)}
              onDownloadLog={() => openUrl(logUrl)}
              isBusy={isBusy}
              canProcess={canProcess}
              hasResult={hasResult}
              selectedFileName={selectedFileName}
              jobId={jobId}
              runId={runId}
              status={status}
            />
            <LogPanel auditLog={auditLog} onDownloadLog={() => openUrl(logUrl)} />
            <HistoryPanel items={jobHistory} />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
