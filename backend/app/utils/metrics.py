from typing import Tuple
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr


def load_as_gray(path: str) -> np.ndarray:
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Unable to load image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def compute_psnr_ssim(reference: np.ndarray, target: np.ndarray) -> dict[str, float]:
    # ensure same size
    if reference.shape != target.shape:
        target = cv2.resize(target, (reference.shape[1], reference.shape[0]), interpolation=cv2.INTER_CUBIC)

    # convert to float in range 0..1 for ssim
    ref_f = reference.astype(np.float32) / 255.0
    tgt_f = target.astype(np.float32) / 255.0

    s = float(ssim(ref_f, tgt_f, data_range=1.0))
    p = float(psnr(ref_f, tgt_f, data_range=1.0))
    return {"ssim": round(s, 4), "psnr": round(p, 2)}


def compare_images_by_path(ref_path: str, tgt_path: str) -> dict[str, float]:
    ref = load_as_gray(ref_path)
    tgt = load_as_gray(tgt_path)
    return compute_psnr_ssim(ref, tgt)
