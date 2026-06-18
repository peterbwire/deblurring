"""Optional supervised restoration model hook.

The restorer is deliberately optional: the classical pipeline keeps working
when no model is configured, while a configured ONNX image-to-image model can
run as an extra restoration pass.
"""

import os
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np


MODEL_PATH_ENV = "FORENSICLEAR_MODEL_PATH"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "restoration.onnx"


class SupervisedRestorer:
    def __init__(self, model_path: Optional[str] = None):
        configured_path = model_path or os.getenv(MODEL_PATH_ENV)
        self.model_path = str(Path(configured_path)) if configured_path else str(DEFAULT_MODEL_PATH)
        self.backend = None
        self.model = None
        self.input_name: str | None = None
        self.output_name: str | None = None
        self.input_shape: list[Any] | None = None
        self.input_type: str = "tensor(float)"

        try:
            import onnxruntime as ort

            self.backend = "onnx"
            self.ort = ort
        except Exception:
            try:
                import torch

                self.backend = "torch"
                self.torch = torch
            except Exception:
                self.backend = None

    def is_available(self) -> bool:
        return self.backend is not None and self.model_path is not None and Path(self.model_path).exists()

    def load(self) -> bool:
        if not self.is_available():
            return False
        try:
            if self.backend == "onnx":
                sess = self.ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
                self.model = sess
                model_input = sess.get_inputs()[0]
                model_output = sess.get_outputs()[0]
                self.input_name = model_input.name
                self.output_name = model_output.name
                self.input_shape = list(model_input.shape or [])
                self.input_type = getattr(model_input, "type", "tensor(float)")
            elif self.backend == "torch":
                self.model = self.torch.load(self.model_path, map_location="cpu")
                self.model.eval()
            return True
        except Exception:
            self.model = None
            return False

    def restore(self, image: np.ndarray) -> np.ndarray:
        """Apply the model to the image and return restored image.

        Expects and returns the pipeline's BGR uint8 image representation.
        """
        if self.model is None and not self.load():
            return image

        if self.backend == "onnx":
            return self._restore_onnx(image)

        if self.backend == "torch":
            return self._restore_torch(image)

        return image

    def _restore_onnx(self, image: np.ndarray) -> np.ndarray:
        original_height, original_width = image.shape[:2]
        input_array, resized_shape = self._preprocess_onnx_input(image)
        input_name = self.input_name or self.model.get_inputs()[0].name
        output = self.model.run([self.output_name] if self.output_name else None, {input_name: input_array})[0]
        restored = self._postprocess_onnx_output(output, resized_shape)

        if restored.shape[:2] != (original_height, original_width):
            restored = cv2.resize(restored, (original_width, original_height), interpolation=cv2.INTER_CUBIC)

        return restored

    def _restore_torch(self, image: np.ndarray) -> np.ndarray:
        with self.torch.no_grad():
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            tensor = self.torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0)
            output = self.model(tensor)
            if isinstance(output, (list, tuple)):
                output = output[0]
            restored = output.detach().cpu().numpy()
        return self._postprocess_onnx_output(restored, image.shape[:2])

    def _preprocess_onnx_input(self, image: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        target_height, target_width = self._static_input_size()
        if target_height and target_width and (target_height, target_width) != image.shape[:2]:
            rgb = cv2.resize(rgb, (target_width, target_height), interpolation=cv2.INTER_AREA)

        if "uint8" in self.input_type:
            array = rgb.transpose(2, 0, 1)[None, ...].astype(np.uint8)
        else:
            array = (rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[None, ...]

        return array, rgb.shape[:2]

    def _static_input_size(self) -> tuple[int | None, int | None]:
        if not self.input_shape or len(self.input_shape) != 4:
            return None, None

        channels_first = self.input_shape[1] in (1, 3) or not isinstance(self.input_shape[1], int)
        if channels_first:
            height, width = self.input_shape[2], self.input_shape[3]
        else:
            height, width = self.input_shape[1], self.input_shape[2]

        if isinstance(height, int) and isinstance(width, int) and height > 0 and width > 0:
            return height, width
        return None, None

    def _postprocess_onnx_output(self, output: np.ndarray, fallback_shape: tuple[int, int]) -> np.ndarray:
        array = np.asarray(output)
        if array.ndim == 4:
            array = array[0]
        if array.ndim == 3 and array.shape[0] in (1, 3):
            array = array.transpose(1, 2, 0)
        if array.ndim == 2:
            array = array[:, :, None]

        if array.dtype != np.uint8:
            array = array.astype(np.float32)
            if array.min(initial=0.0) < -0.05:
                array = (array + 1.0) / 2.0
            if array.max(initial=0.0) <= 1.5:
                array = array * 255.0
            array = np.clip(array, 0, 255).astype(np.uint8)

        if array.shape[2] == 1:
            array = np.repeat(array, 3, axis=2)
        elif array.shape[2] > 3:
            array = array[:, :, :3]

        if array.shape[:2] != fallback_shape:
            array = cv2.resize(array, (fallback_shape[1], fallback_shape[0]), interpolation=cv2.INTER_CUBIC)

        return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)

    def model_summary(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "configured": self.model_path is not None,
            "available": self.is_available(),
            "model_file": Path(self.model_path).name if self.model_path else None,
        }


default_restorer = SupervisedRestorer()
# auto-load if a path is configured
try:
    if default_restorer.is_available():
        default_restorer.load()
except Exception:
    pass
