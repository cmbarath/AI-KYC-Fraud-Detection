"""Vercel-only Pillow bridge for EasyOCR's narrow scikit-image dependency.

The deployed Python bundle lacks scikit-image's adjacent ``__init__.pyi``,
which lazy-loader requires during import. EasyOCR 1.7.2 only uses
``skimage.io.imread`` in its image-loading path. The temporary shim is removed
after EasyOCR imports so unrelated code does not see a substitute skimage
package.
"""

import importlib
import os
import sys
from io import BytesIO
from types import ModuleType
from typing import BinaryIO

import numpy as np
from PIL import Image


def pillow_imread(
    source: str | os.PathLike[str] | bytes | BinaryIO,
) -> np.ndarray:
    if isinstance(source, bytes):
        source = BytesIO(source)

    with Image.open(source) as image:
        return np.array(image.convert("RGB"), copy=True)


def import_easyocr() -> ModuleType:
    if os.getenv("VERCEL") != "1":
        return importlib.import_module("easyocr")
    if "easyocr" in sys.modules:
        return sys.modules["easyocr"]
    if "skimage" in sys.modules or "skimage.io" in sys.modules:
        return importlib.import_module("easyocr")

    skimage_module = ModuleType("skimage")
    setattr(skimage_module, "__path__", [])
    io_module = ModuleType("skimage.io")
    setattr(io_module, "__package__", "skimage")
    setattr(io_module, "imread", pillow_imread)
    setattr(skimage_module, "io", io_module)

    sys.modules["skimage"] = skimage_module
    sys.modules["skimage.io"] = io_module
    try:
        return importlib.import_module("easyocr")
    finally:
        if sys.modules.get("skimage.io") is io_module:
            del sys.modules["skimage.io"]
        if sys.modules.get("skimage") is skimage_module:
            del sys.modules["skimage"]
