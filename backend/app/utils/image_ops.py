import os

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from skimage.restoration import estimate_sigma
from skimage.restoration import richardson_lucy


MAX_IMAGE_PIXELS = int(os.getenv("FORENSICLEAR_MAX_IMAGE_PIXELS", "40000000"))


def validate_image_file(path: str) -> dict[str, int | str]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            normalized = ImageOps.exif_transpose(image)
            pixel_count = normalized.width * normalized.height
            if pixel_count > MAX_IMAGE_PIXELS:
                raise ValueError("Uploaded image exceeds the maximum allowed pixel count.")
            return {
                "width": normalized.width,
                "height": normalized.height,
                "format": normalized.format or image.format or "unknown",
            }
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Uploaded file is not a readable image.") from exc


def load_image(path: str) -> np.ndarray:
    try:
        with Image.open(path) as image:
            normalized = ImageOps.exif_transpose(image)
            if normalized.mode == "P":
                normalized = normalized.convert("RGBA")
            elif normalized.mode == "LA":
                normalized = normalized.convert("RGBA")
            elif normalized.mode not in {"RGB", "RGBA", "L"}:
                normalized = normalized.convert("RGB")

            array = np.array(normalized)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Unable to load image data.") from exc

    if array.ndim == 2:
        return array
    if array.shape[2] == 4:
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGRA)
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)


def save_image(path: str, image: np.ndarray) -> None:
    extension = "." + path.split(".")[-1]
    success, encoded = cv2.imencode(extension, image)
    if not success:
        raise ValueError("Unable to encode processed image.")
    encoded.tofile(path)


def split_alpha(image: np.ndarray) -> tuple[np.ndarray, np.ndarray | None, str]:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), None, "gray"
    if image.shape[2] == 4:
        return image[:, :, :3], image[:, :, 3], "bgra"
    return image, None, "bgr"


def merge_alpha(image: np.ndarray, alpha: np.ndarray | None, original_mode: str) -> np.ndarray:
    if original_mode == "gray":
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if original_mode == "bgra" and alpha is not None:
        return np.dstack((image, alpha))
    return image


def resize_alpha(alpha: np.ndarray | None, scale_factor: int) -> np.ndarray | None:
    if alpha is None:
        return None
    height, width = alpha.shape[:2]
    return cv2.resize(alpha, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_LINEAR)


def denoise_image(image: np.ndarray, strength: str) -> np.ndarray:
    params = {
        "low": {"h": 4, "h_color": 4, "template": 7, "search": 21},
        "medium": {"h": 7, "h_color": 7, "template": 7, "search": 21},
        "high": {"h": 11, "h_color": 11, "template": 7, "search": 21},
    }
    config = params[strength]
    return cv2.fastNlMeansDenoisingColored(
        image,
        None,
        config["h"],
        config["h_color"],
        config["template"],
        config["search"],
    )


def apply_unsharp_mask(image: np.ndarray, sigma: float, amount: float) -> np.ndarray:
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma, sigmaY=sigma)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def approximate_deconvolution(image: np.ndarray, weight: float) -> np.ndarray:
    kernel = np.array(
        [
            [0.0, -weight, 0.0],
            [-weight, 1.0 + (4.0 * weight), -weight],
            [0.0, -weight, 0.0],
        ],
        dtype=np.float32,
    )
    restored = cv2.filter2D(image, -1, kernel)
    return np.clip(restored, 0, 255).astype(np.uint8)


def edge_aware_sharpen(image: np.ndarray, edge_weight: float) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, threshold1=40, threshold2=140)
    edge_mask = cv2.GaussianBlur(edges, (0, 0), sigmaX=1.2)
    edge_mask = cv2.cvtColor(edge_mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
    smoothed = cv2.bilateralFilter(image, d=7, sigmaColor=40, sigmaSpace=40)
    detail = image.astype(np.float32) - smoothed.astype(np.float32)
    enhanced = image.astype(np.float32) + (detail * edge_mask * edge_weight * 2.2)
    return np.clip(enhanced, 0, 255).astype(np.uint8)


def apply_clahe_luminance(image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def upscale_image(image: np.ndarray, scale_factor: int) -> np.ndarray:
    height, width = image.shape[:2]
    return cv2.resize(image, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)


def estimate_noise(image: np.ndarray) -> float:
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    sigma = estimate_sigma(rgb_image, channel_axis=-1, average_sigmas=True)
    return float(sigma)


def _gaussian_psf(size: int, sigma: float) -> np.ndarray:
    """Generate a normalized 2D Gaussian PSF kernel."""
    if size % 2 == 0:
        size += 1
    ax = np.arange(-size // 2 + 1.0, size // 2 + 1.0)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
    kernel /= np.sum(kernel)
    return kernel.astype(np.float32)


def lucy_richardson_deconvolution(image: np.ndarray, psf_sigma: float = 1.5, iterations: int = 30) -> np.ndarray:
    """Perform Lucy-Richardson deconvolution on a BGR image.

    This applies the algorithm per-channel and returns an 8-bit BGR image.
    """
    if image.ndim == 2 or image.shape[2] == 1:
        gray = image.astype(np.float32) / 255.0
        psf_size = max(3, int(psf_sigma * 6))
        psf = _gaussian_psf(psf_size, psf_sigma)
        restored = richardson_lucy(gray, psf, num_iter=iterations)
        restored = np.clip(restored * 255.0, 0, 255).astype(np.uint8)
        return restored

    # color image: split channels and process independently
    b, g, r = cv2.split(image)
    channels = []
    psf_size = max(3, int(psf_sigma * 6))
    psf = _gaussian_psf(psf_size, psf_sigma)
    for ch in (b, g, r):
        arr = ch.astype(np.float32) / 255.0
        restored_ch = richardson_lucy(arr, psf, num_iter=iterations)
        restored_ch = np.clip(restored_ch * 255.0, 0, 255).astype(np.uint8)
        channels.append(restored_ch)

    restored = cv2.merge(tuple(channels))
    return restored


def multi_scale_deblur(image: np.ndarray, psf_sigma: float = 1.5, iterations: int = 20, levels: int = 2) -> np.ndarray:
    """Multi-scale deblurring: deconvolve at lower resolution then refine at full size."""
    working = image.copy()
    # Downscale
    small = working.copy()
    for _ in range(levels):
        small = cv2.pyrDown(small)

    # Apply LR on small
    small_restored = lucy_richardson_deconvolution(small, psf_sigma=max(0.7, psf_sigma / 2.0), iterations=max(8, iterations // 2))

    # Upscale back
    up = small_restored
    for _ in range(levels):
        up = cv2.pyrUp(up)

    # Resize exactly to original
    up = cv2.resize(up, (working.shape[1], working.shape[0]), interpolation=cv2.INTER_CUBIC)

    # Blend with original to avoid over-sharpening
    blended = cv2.addWeighted(working.astype(np.float32), 0.6, up.astype(np.float32), 0.4, 0)
    return np.clip(blended, 0, 255).astype(np.uint8)
