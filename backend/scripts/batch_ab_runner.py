"""Batch A/B runner: for each provided job_id, run two restorations (baseline + improved)
and record PSNR/SSIM results to a CSV.

Usage:
  python batch_ab_runner.py job1 job2 ...
Output: results.csv in working directory
"""
import csv
import sys
from pathlib import Path

from app.models.schemas import ProcessRequest
from app.services.file_manager import get_original_file, get_run_output_path
from app.services.image_pipeline import process_image
from app.utils.metrics import compare_images_by_path


def run_for_job(job_id: str, run_suffix: str, settings: ProcessRequest):
    run_id = f"batch-{run_suffix}"
    original_path = get_original_file(job_id)
    result = process_image(job_id, run_id, original_path, settings)
    return result["output_path"]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: batch_ab_runner.py <job_id> [<job_id> ...]")
        return 2

    jobs = argv[1:]
    rows = []

    baseline_settings = ProcessRequest(denoise_strength="medium", deblur_mode="standard", sharpen_edges=True, upscale="none", evidence_safe=False)
    improved_settings = ProcessRequest(denoise_strength="medium", deblur_mode="aggressive", sharpen_edges=True, upscale="none", evidence_safe=False, deblur_iterations=20, psf_sigma=1.4)

    for job in jobs:
        try:
            base_out = run_for_job(job, "base", baseline_settings)
            imp_out = run_for_job(job, "improved", improved_settings)
            metrics = compare_images_by_path(str(base_out), str(imp_out))
            rows.append({"job_id": job, "ssim": metrics["ssim"], "psnr": metrics["psnr"]})
            print(f"{job}: SSIM={metrics['ssim']} PSNR={metrics['psnr']}")
        except Exception as exc:
            print(f"Failed for job {job}: {exc}")

    csv_path = Path.cwd() / "ab_results.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["job_id", "ssim", "psnr"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {csv_path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
