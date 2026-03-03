"""Orbitals tiling engine — strategies, blending, preview, and tile plan types."""

from .plan import TilePlan, TileInfo
from .strategies import (
    compute_tile_positions,
    plan_auto,
    plan_uniform,
    plan_grid,
    plan_padded,
)
from .blending import create_weight_mask
from .preview import render_tile_preview

__all__ = [
    "TilePlan",
    "TileInfo",
    "compute_tile_positions",
    "plan_auto",
    "plan_uniform",
    "plan_grid",
    "plan_padded",
    "create_weight_mask",
    "render_tile_preview",
]
