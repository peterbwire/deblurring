"""Optional supervised restoration model hook.

This module provides a lightweight wrapper that can be expanded to load a
PyTorch or ONNX model for learned image restoration. It is intentionally
dependency-light: if neither runtime is available it remains disabled.
"""
from typing import Optional
import numpy as np


import os


class SupervisedRestorer:
    def __init__(self, model_path: Optional[str] = None):
        # allow model path to be provided or read from env
        self.model_path = model_path or os.getenv("FORENSICLEAR_MODEL_PATH")
        self.backend = None
        self.model = None
        # Try to detect a runtime; prefer onnxruntime if available
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
        return self.backend is not None and self.model_path is not None

    def load(self) -> bool:
        if not self.is_available():
            return False
        try:
            if self.backend == "onnx":
                sess = self.ort.InferenceSession(self.model_path)
                self.model = sess
            elif self.backend == "torch":
                self.model = self.torch.load(self.model_path, map_location="cpu")
                self.model.eval()
            return True
        except Exception:
            self.model = None
            return False

    def restore(self, image: np.ndarray) -> np.ndarray:
        """Apply the model to the image and return restored image.

        Currently a no-op if the model isn't loaded; extend for real models.
        """
        if self.model is None:
            return image
        # Placeholder: users should implement model preprocessing/inference here
        return image


default_restorer = SupervisedRestorer()
# auto-load if a path is configured
try:
    if default_restorer.is_available():
        default_restorer.load()
except Exception:
    pass
