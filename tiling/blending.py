"""Weight-mask generation for seamless tile merging.

Each tile gets a 2-D weight mask that ramps smoothly in overlap regions.
Image-edge tiles have no ramp on their boundary side (weight stays 1.0),
preserving original pixels at the canvas edges.
"""

from __future__ import annotations

import numpy as np
from .plan import TilePlan, TileInfo


def _cosine_ramp(length: int) -> np.ndarray:
    """Cosine ramp from 0 → 1 over *length* pixels."""
    if length <= 0:
        return np.empty(0, dtype=np.float64)
    t = np.linspace(0.0, 1.0, length, dtype=np.float64)
    return 0.5 * (1.0 - np.cos(np.pi * t))


def _linear_ramp(length: int) -> np.ndarray:
    """Linear ramp from 0 → 1 over *length* pixels."""
    if length <= 0:
        return np.empty(0, dtype=np.float64)
    return np.linspace(0.0, 1.0, length, dtype=np.float64)


def create_weight_mask(
    tile_info: TileInfo,
    plan: TilePlan,
    blend_mode: str = "cosine",
    blend_strength: float = 1.0,
) -> np.ndarray:
    """Build a 2-D weight mask for *tile_info* within *plan*.

    Parameters
    ----------
    tile_info:
        The tile whose mask to generate.
    plan:
        The overall tiling plan (provides grid extents and overlap).
    blend_mode:
        ``"cosine"`` (default), ``"linear"``, or ``"none"``.
    blend_strength:
        Scale factor for the ramp length (0 = hard cut, 1 = full ramp).

    Returns
    -------
    numpy.ndarray
        Shape ``(tile_h, tile_w)`` with values in ``[0, 1]``.
    """
    tile_w, tile_h = tile_info.size
    col, row = tile_info.grid_pos
    n_cols, n_rows = plan.grid
    ov_x, ov_y = plan.overlap

    weight = np.ones((tile_h, tile_w), dtype=np.float64)

    if blend_mode == "none" or blend_strength <= 0:
        return weight

    # Effective ramp lengths (scaled by blend_strength).
    ramp_x = max(1, int(ov_x * blend_strength)) if ov_x > 0 else 0
    ramp_y = max(1, int(ov_y * blend_strength)) if ov_y > 0 else 0

    ramp_fn = _cosine_ramp if blend_mode == "cosine" else _linear_ramp

    # ── horizontal ramps ──────────────────────────────────────────
    if col > 0 and ramp_x > 0:
        length = min(ramp_x, tile_w)
        ramp = ramp_fn(length)
        weight[:, :length] *= ramp[np.newaxis, :]

    if col < n_cols - 1 and ramp_x > 0:
        length = min(ramp_x, tile_w)
        ramp = ramp_fn(length)[::-1]
        weight[:, tile_w - length:] *= ramp[np.newaxis, :]

    # ── vertical ramps ────────────────────────────────────────────
    if row > 0 and ramp_y > 0:
        length = min(ramp_y, tile_h)
        ramp = ramp_fn(length)
        weight[:length, :] *= ramp[:, np.newaxis]

    if row < n_rows - 1 and ramp_y > 0:
        length = min(ramp_y, tile_h)
        ramp = ramp_fn(length)[::-1]
        weight[tile_h - length:, :] *= ramp[:, np.newaxis]

    return weight
