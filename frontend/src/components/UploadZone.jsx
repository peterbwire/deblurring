import { useState } from "react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";

const maxFileSize = 15 * 1024 * 1024;

export default function UploadZone({
  onFileAccepted,
  isBusy,
  isDisabled,
  selectedFileName,
  errorMessage,
}) {
  const [localError, setLocalError] = useState("");

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
    },
    maxSize: maxFileSize,
    multiple: false,
    disabled: isBusy || isDisabled,
    onDropAccepted: (files) => {
      setLocalError("");
      if (files[0]) {
        onFileAccepted(files[0]);
      }
    },
    onDropRejected: (rejections) => {
      const firstRejection = rejections[0];
      const firstError = firstRejection?.errors?.[0];

      if (firstError?.code === "file-too-large") {
        setLocalError("That file exceeds the 15 MB upload limit.");
        return;
      }

      if (firstError?.code === "file-invalid-type") {
        setLocalError("Unsupported file type. Please upload JPG, JPEG, PNG, or WEBP.");
        return;
      }

      setLocalError("That file could not be accepted. Please choose a supported image.");
    },
  });

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05, duration: 0.45 }}
      className="glass-panel rounded-[28px] p-6 sm:p-7"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="section-title text-xl font-semibold text-white">Upload Source Image</p>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-300">
            Supported formats: JPG, JPEG, PNG, WEBP. Original uploads are preserved untouched for
            comparison and evidentiary review.
          </p>
        </div>
        <div className="status-pill">Max 15 MB</div>
      </div>

      <div
        {...getRootProps()}
        className={`mt-6 rounded-[28px] border border-dashed px-6 py-10 text-center transition ${
          isDragActive
            ? "border-cyan-300 bg-cyan-400/10 shadow-glow"
            : "border-cyan-200/15 bg-slate-950/35 hover:border-cyan-200/30 hover:bg-slate-950/45"
        } ${isBusy || isDisabled ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
      >
        <input {...getInputProps()} />
        <div className="mx-auto max-w-md">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-200/15 bg-cyan-300/10 text-cyan-100">
            <span className="text-2xl">+</span>
          </div>
          <p className="mt-5 text-lg font-semibold text-white">
            {isDragActive ? "Release to upload your image" : "Drag and drop an image here"}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {isDisabled
              ? "Authenticate to unlock upload and processing."
              : isBusy
              ? "Upload or processing is in progress."
              : "Or click to browse your local files and create a new restoration job."}
          </p>
          {selectedFileName ? (
            <div className="mt-5 inline-flex rounded-full border border-cyan-300/15 bg-cyan-300/10 px-4 py-2 text-sm text-cyan-50">
              Preserved source: {selectedFileName}
            </div>
          ) : null}
        </div>
      </div>

      {errorMessage || localError ? (
        <div className="mt-4 rounded-2xl border border-rose-300/15 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
          {localError || errorMessage}
        </div>
      ) : null}
    </motion.section>
  );
}
