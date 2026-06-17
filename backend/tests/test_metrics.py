import numpy as np
from app.utils.metrics import compute_psnr_ssim


def test_identical_images():
    a = (np.ones((64, 64), dtype=np.uint8) * 128)
    b = a.copy()
    metrics = compute_psnr_ssim(a, b)
    assert metrics["ssim"] == 1.0
    assert metrics["psnr"] == float("inf") or metrics["psnr"] > 100
