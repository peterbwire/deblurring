from pathlib import Path

import numpy as np

from app.services.supervised_model import SupervisedRestorer


class FakeOnnxValue:
    def __init__(self, name, shape=None, value_type="tensor(float)"):
        self.name = name
        self.shape = shape or [1, 3, "height", "width"]
        self.type = value_type


class FakeOnnxSession:
    def __init__(self, output_transform=None):
        self.output_transform = output_transform or (lambda array: array)

    def get_inputs(self):
        return [FakeOnnxValue("input")]

    def get_outputs(self):
        return [FakeOnnxValue("output")]

    def run(self, output_names, feeds):
        return [self.output_transform(feeds["input"])]


def make_restorer(session):
    restorer = SupervisedRestorer(model_path=str(Path("unused.onnx")))
    restorer.backend = "onnx"
    restorer.model = session
    restorer.input_name = "input"
    restorer.output_name = "output"
    restorer.input_shape = [1, 3, "height", "width"]
    restorer.input_type = "tensor(float)"
    return restorer


def test_onnx_restore_preserves_bgr_image_for_identity_model():
    image = np.zeros((8, 10, 3), dtype=np.uint8)
    image[:, :, 0] = 25
    image[:, :, 1] = 100
    image[:, :, 2] = 210

    restored = make_restorer(FakeOnnxSession()).restore(image)

    assert restored.shape == image.shape
    assert np.array_equal(restored, image)


def test_onnx_restore_resizes_static_model_output_back_to_original_size():
    def brighten(array):
        return np.clip(array + 0.25, 0.0, 1.0)

    image = np.ones((12, 16, 3), dtype=np.uint8) * 60
    restorer = make_restorer(FakeOnnxSession(output_transform=brighten))
    restorer.input_shape = [1, 3, 6, 8]

    restored = restorer.restore(image)

    assert restored.shape == image.shape
    assert restored.mean() > image.mean()
