import time
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageOps

from app.models.schemas import ProcessRequest
from app.services.file_manager import calculate_file_sha256, get_run_output_path, read_job_manifest
from app.services.logger_service import current_timestamp, write_audit_log
from app.utils.image_ops import (
    apply_clahe_luminance,
    apply_unsharp_mask,
    approximate_deconvolution,
    denoise_image,
    edge_aware_sharpen,
    estimate_noise,
    load_image,
    merge_alpha,
    resize_alpha,
    save_image,
    split_alpha,
    upscale_image,
)


EVIDENCE_WARNING = (
    "Output is enhanced for visibility and should not be treated as exact reconstruction of lost detail."
)
PIPELINE_VERSION = "2026.03.14-hardened"


def inspect_image(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        normalized = ImageOps.exif_transpose(image)
        metadata_keys = sorted(list(image.info.keys()))
        return {
            "format": image.format,
            "mode": image.mode,
            "raw_dimensions": {"width": image.width, "height": image.height},
            "normalized_dimensions": {"width": normalized.width, "height": normalized.height},
            "metadata_keys": metadata_keys[:10],
        }


def unique_messages(messages: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for message in messages:
        if message not in seen:
            seen.add(message)
            ordered.append(message)
    return ordered


def get_effective_settings(settings: ProcessRequest) -> tuple[str, str]:
    denoise_strength = settings.denoise_strength
    deblur_mode = settings.deblur_mode

    if settings.evidence_safe and denoise_strength == "high":
        denoise_strength = "medium"
    if settings.evidence_safe and deblur_mode == "aggressive":
        deblur_mode = "standard"

    return denoise_strength, deblur_mode


def process_image(
    job_id: str,
    run_id: str,
    original_path: Path,
    settings: ProcessRequest,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    def report_progress(phase: str) -> None:
        if progress_callback:
            progress_callback(phase)

    started_at = time.perf_counter()
    report_progress("inspecting_original")
    manifest = read_job_manifest(job_id)
    inspection = inspect_image(original_path)

    report_progress("loading_original")
    raw_image = load_image(str(original_path))
    working_image, alpha_channel, source_mode = split_alpha(raw_image)
    original_height, original_width = working_image.shape[:2]

    warnings: list[str] = []
    steps: list[str] = []
    requested_settings = settings.model_dump()
    effective_denoise, effective_deblur = get_effective_settings(settings)
    estimated_noise = estimate_noise(working_image)

    if settings.evidence_safe:
        steps.append("Evidence-safe mode enabled.")
        warnings.append(EVIDENCE_WARNING)
        if effective_denoise != settings.denoise_strength or effective_deblur != settings.deblur_mode:
            steps.append("Aggressive settings were reduced to conservative levels.")

    report_progress("denoising")
    working_image = denoise_image(working_image, effective_denoise)
    steps.append(f"Applied non-local means denoising ({effective_denoise}).")

    deblur_profiles = {
        "mild": {"sigma": 1.0, "amount": 0.65, "edge_weight": 0.18, "deconv_weight": 0.0},
        "standard": {"sigma": 1.3, "amount": 1.0, "edge_weight": 0.28, "deconv_weight": 0.12},
        "aggressive": {"sigma": 1.6, "amount": 1.45, "edge_weight": 0.4, "deconv_weight": 0.22},
    }
    profile = deblur_profiles[effective_deblur]

    report_progress("deblurring")
    working_image = apply_unsharp_mask(working_image, sigma=profile["sigma"], amount=profile["amount"])
    steps.append(f"Applied conservative unsharp mask ({effective_deblur}).")

    if settings.sharpen_edges:
        edge_weight = min(profile["edge_weight"], 0.24) if settings.evidence_safe else profile["edge_weight"]
        working_image = edge_aware_sharpen(working_image, edge_weight=edge_weight)
        steps.append("Applied edge-aware sharpening.")

    if profile["deconv_weight"] > 0 and not settings.evidence_safe:
        working_image = approximate_deconvolution(working_image, weight=profile["deconv_weight"])
        steps.append("Applied light deconvolution-inspired kernel restoration.")
    elif profile["deconv_weight"] > 0 and settings.evidence_safe:
        steps.append("Skipped deconvolution-inspired restoration due to evidence-safe mode.")

    report_progress("contrast_balancing")
    clahe_clip = 1.6 if settings.evidence_safe else 2.0
    working_image = apply_clahe_luminance(working_image, clip_limit=clahe_clip)
    steps.append("Enhanced luminance contrast with gentle CLAHE.")

    output_scale = 1
    if settings.upscale == "2x":
        report_progress("upscaling")
        output_scale = 2
        working_image = upscale_image(working_image, scale_factor=2)
        alpha_channel = resize_alpha(alpha_channel, scale_factor=2)
        steps.append("Upscaled image 2x using high-quality cubic interpolation.")
        warnings.append("Upscaling increases size for inspection but does not recreate missing detail.")

    report_progress("writing_artifacts")
    final_image = merge_alpha(working_image, alpha_channel, source_mode)
    output_path = get_run_output_path(job_id, run_id, suffix=".png")
    save_image(str(output_path), final_image)
    output_sha256 = calculate_file_sha256(output_path)

    duration_seconds = round(time.perf_counter() - started_at, 3)
    output_height, output_width = working_image.shape[:2]

    if estimated_noise > 0.08:
        warnings.append("High sensor noise was detected; restored output may still retain texture artifacts.")
    if inspection["normalized_dimensions"]["width"] < 640 or inspection["normalized_dimensions"]["height"] < 640:
        warnings.append("Small source dimensions limit the recoverable detail in the enhanced output.")

    audit_log = {
        "job_id": job_id,
        "run_id": run_id,
        "original_filename": manifest["original_filename"],
        "timestamp": current_timestamp(),
        "pipeline_version": PIPELINE_VERSION,
        "original_sha256": manifest["sha256"],
        "output_sha256": output_sha256,
        "original_dimensions": {
            "width": original_width,
            "height": original_height,
        },
        "output_dimensions": {
            "width": output_width,
            "height": output_height,
        },
        "denoise_strength_used": effective_denoise,
        "deblur_mode_used": effective_deblur,
        "sharpen_enabled": settings.sharpen_edges,
        "upscale_setting": settings.upscale,
        "evidence_safe": settings.evidence_safe,
        "processing_steps_applied": steps,
        "warnings": unique_messages(warnings),
        "runtime_seconds": duration_seconds,
        "estimated_noise_sigma": round(estimated_noise, 4),
        "requested_settings": requested_settings,
        "inspection": inspection,
        "output_scale_factor": output_scale,
        "future_model_placeholder": {
            "enabled": False,
            "notes": "PyTorch model hooks can be added here for supervised restoration models in a later phase.",
        },
    }
    log_path = write_audit_log(job_id, run_id, audit_log)

    return {
        "job_id": job_id,
        "run_id": run_id,
        "output_path": output_path,
        "log_path": log_path,
        "warnings": audit_log["warnings"],
        "duration_seconds": duration_seconds,
        "audit_log": audit_log,
        "output_sha256": output_sha256,
    }
