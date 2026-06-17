"""Compare two restored images (A/B) using SSIM and PSNR.

Usage:
    python compare_restorations.py <reference_image> <target_image>
"""
import sys
from pathlib import Path
from app.utils.metrics import compare_images_by_path


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("Usage: compare_restorations.py <reference_image> <target_image>")
        return 2
    ref = Path(argv[1])
    tgt = Path(argv[2])
    if not ref.exists() or not tgt.exists():
        print("Provided files must exist.")
        return 3
    metrics = compare_images_by_path(str(ref), str(tgt))
    print(f"Comparison results:\n  SSIM: {metrics['ssim']}\n  PSNR: {metrics['psnr']} dB")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
