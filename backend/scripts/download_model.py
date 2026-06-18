"""Download a direct ONNX restoration model for the supervised pipeline.

Usage:
  python scripts/download_model.py --url https://.../model.onnx

The app loads ``backend/models/restoration.onnx`` by default. You can override
the runtime path with ``FORENSICLEAR_MODEL_PATH``.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path


DEFAULT_MODEL_URL_ENV = "FORENSICLEAR_MODEL_URL"
DEFAULT_OUTPUT_NAME = "restoration.onnx"


def download_file(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"Model already exists at {output_path}")
        return output_path

    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    print(f"Downloading ONNX model from {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        with temp_path.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)

    temp_path.replace(output_path)
    print(f"Downloaded model to {output_path}")
    return output_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download an ONNX restoration model.")
    parser.add_argument(
        "--url",
        default=os.getenv(DEFAULT_MODEL_URL_ENV),
        help=f"Direct .onnx URL. Defaults to {DEFAULT_MODEL_URL_ENV}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "models" / DEFAULT_OUTPUT_NAME,
        help="Output path for the ONNX model.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.url:
        print(
            "No model URL provided. Pass --url or set "
            f"{DEFAULT_MODEL_URL_ENV} to a direct .onnx download URL."
        )
        return 2

    output_path = args.output
    if output_path.suffix.lower() != ".onnx":
        print("Output path must end in .onnx")
        return 2

    if args.force and output_path.exists():
        output_path.unlink()

    try:
        model_path = download_file(args.url, output_path)
        print("Set FORENSICLEAR_MODEL_PATH to this path if you use a custom location:")
        print(model_path)
        return 0
    except Exception as exc:
        print(f"Download failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
