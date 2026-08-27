from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def render_mask(
    mask: NDArray[np.integer],
    colors: tuple[str, ...],
    destination: Path,
    alpha: int = 190,
) -> None:
    palette = np.array([_hex_to_rgb(color) for color in colors], dtype=np.uint8)
    rgb = palette[mask]
    rgba = np.dstack((rgb, np.full(mask.shape, alpha, dtype=np.uint8)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(destination)


def render_uncertainty(uncertainty: NDArray[np.floating], destination: Path) -> None:
    clipped = np.clip(uncertainty, 0.0, 1.0)
    low = np.array([49, 92, 58], dtype=np.float32)
    high = np.array([190, 126, 26], dtype=np.float32)
    rgb = low[None, None, :] + clipped[..., None] * (high - low)[None, None, :]
    alpha = (48 + clipped * 180).astype(np.uint8)
    rgba = np.dstack((rgb.astype(np.uint8), alpha))
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(destination)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    stripped = value.lstrip("#")
    if len(stripped) != 6:
        raise ValueError(f"Expected six-digit hex color, received {value}")
    return tuple(int(stripped[index : index + 2], 16) for index in (0, 2, 4))
