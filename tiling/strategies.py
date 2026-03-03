"""Tiling strategies — compute tile grids for each mode.

Every public ``plan_*`` function returns a fully populated :class:`TilePlan`.
"""

from __future__ import annotations

import math
from .plan import TilePlan, TileInfo


# ── helpers ──────────────────────────────────────────────────────────

def _round_up(value: int, divisor: int) -> int:
    """Round *value* up to the nearest multiple of *divisor*."""
    if divisor <= 1:
        return value
    return ((value + divisor - 1) // divisor) * divisor


def _round_down(value: int, divisor: int) -> int:
    """Round *value* down to the nearest multiple of *divisor*."""
    if divisor <= 1:
        return value
    return (value // divisor) * divisor


def compute_tile_positions(image_size: int, tile_size: int, overlap: int) -> list[int]:
    """Clamped-to-bounds tile placement.  **No slivers.**

    The last tile's start is clamped to ``image_size - tile_size`` so every
    tile is exactly ``tile_size`` pixels.  The penultimate–last overlap may
    exceed *overlap*, but the blending masks handle that gracefully.
    """
    if tile_size >= image_size:
        return [0]

    stride = tile_size - overlap
    if stride <= 0:
        raise ValueError(
            f"overlap ({overlap}) must be smaller than tile_size ({tile_size})"
        )

    n = max(1, math.ceil((image_size - tile_size) / stride) + 1)
    positions: list[int] = []
    for i in range(n):
        pos = min(i * stride, image_size - tile_size)
        positions.append(pos)

    # Deduplicate in case clamping creates duplicates at the end.
    seen: set[int] = set()
    unique: list[int] = []
    for p in positions:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _build_tile_list(
    col_positions: list[int],
    row_positions: list[int],
    tile_w: int,
    tile_h: int,
) -> list[TileInfo]:
    """Create an ordered list of :class:`TileInfo` from column/row positions."""
    tiles: list[TileInfo] = []
    idx = 0
    for ri, y in enumerate(row_positions):
        for ci, x in enumerate(col_positions):
            tiles.append(
                TileInfo(
                    index=idx,
                    grid_pos=(ci, ri),
                    position=(x, y),
                    size=(tile_w, tile_h),
                )
            )
            idx += 1
    return tiles


# ── strategies ───────────────────────────────────────────────────────

def plan_uniform(
    image_w: int,
    image_h: int,
    tile_w: int,
    tile_h: int,
    overlap: int,
    divisible_by: int = 8,
) -> TilePlan:
    """Fixed tile size, clamped-to-bounds placement.

    This is the primary "fix" for SeedVR2's sliver problem: all tiles are
    the requested size, and the last tile simply shifts inward.
    """
    tile_w = max(divisible_by, _round_up(tile_w, divisible_by))
    tile_h = max(divisible_by, _round_up(tile_h, divisible_by))
    overlap_aligned = _round_down(min(overlap, min(tile_w, tile_h) - divisible_by), divisible_by)
    overlap_aligned = max(0, overlap_aligned)

    # Clamp tile size to image dimensions — if image is smaller than tile,
    # the single tile is the whole image (rounded up to divisible_by).
    eff_tile_w = min(tile_w, _round_up(image_w, divisible_by))
    eff_tile_h = min(tile_h, _round_up(image_h, divisible_by))

    col_positions = compute_tile_positions(image_w, eff_tile_w, overlap_aligned)
    row_positions = compute_tile_positions(image_h, eff_tile_h, overlap_aligned)

    tiles = _build_tile_list(col_positions, row_positions, eff_tile_w, eff_tile_h)

    return TilePlan(
        strategy="uniform",
        original_size=(image_w, image_h),
        tile_size=(eff_tile_w, eff_tile_h),
        overlap=(overlap_aligned, overlap_aligned),
        grid=(len(col_positions), len(row_positions)),
        divisible_by=divisible_by,
        tiles=tiles,
    )


def plan_grid(
    image_w: int,
    image_h: int,
    rows: int,
    cols: int,
    overlap: int,
    divisible_by: int = 8,
) -> TilePlan:
    """User-specified grid dimensions; tile size derived from image / grid."""
    rows = max(1, rows)
    cols = max(1, cols)

    overlap_aligned = _round_down(overlap, divisible_by)
    overlap_aligned = max(0, overlap_aligned)

    # Derive tile size: each tile must cover its "cell" plus overlap.
    # cell_w = ceil(image_w / cols), then tile_w = cell_w + overlap
    cell_w = math.ceil(image_w / cols)
    cell_h = math.ceil(image_h / rows)
    tile_w = _round_up(cell_w + overlap_aligned, divisible_by)
    tile_h = _round_up(cell_h + overlap_aligned, divisible_by)

    # Clamp tile to image if grid=1x1
    tile_w = min(tile_w, _round_up(image_w, divisible_by))
    tile_h = min(tile_h, _round_up(image_h, divisible_by))

    col_positions = compute_tile_positions(image_w, tile_w, overlap_aligned)
    row_positions = compute_tile_positions(image_h, tile_h, overlap_aligned)

    tiles = _build_tile_list(col_positions, row_positions, tile_w, tile_h)

    return TilePlan(
        strategy="grid",
        original_size=(image_w, image_h),
        tile_size=(tile_w, tile_h),
        overlap=(overlap_aligned, overlap_aligned),
        grid=(len(col_positions), len(row_positions)),
        divisible_by=divisible_by,
        tiles=tiles,
    )


def plan_padded(
    image_w: int,
    image_h: int,
    tile_w: int,
    tile_h: int,
    overlap: int,
    divisible_by: int = 8,
    pad_mode: str = "reflect",
) -> TilePlan:
    """Pad image so grid divides cleanly — all tiles identical, no clamping.

    The untiler is responsible for cropping the padding back off.
    """
    tile_w = max(divisible_by, _round_up(tile_w, divisible_by))
    tile_h = max(divisible_by, _round_up(tile_h, divisible_by))
    overlap_aligned = _round_down(min(overlap, min(tile_w, tile_h) - divisible_by), divisible_by)
    overlap_aligned = max(0, overlap_aligned)

    stride_w = tile_w - overlap_aligned
    stride_h = tile_h - overlap_aligned

    # How many full strides fit?  We need: padded_w = tile_w + k * stride_w
    def _padded_size(img: int, tile: int, stride: int) -> int:
        if tile >= img:
            return tile
        # Minimum k such that tile + k*stride >= img
        k = math.ceil((img - tile) / stride)
        return tile + k * stride

    padded_w = _padded_size(image_w, tile_w, stride_w)
    padded_h = _padded_size(image_h, tile_h, stride_h)

    # Centre the original image within the padded canvas.
    pad_left = (padded_w - image_w) // 2
    pad_top = (padded_h - image_h) // 2
    pad_right = padded_w - image_w - pad_left
    pad_bottom = padded_h - image_h - pad_top

    # Positions are exact — no clamping needed.
    col_positions = [i * stride_w for i in range(math.ceil((padded_w - overlap_aligned) / stride_w))]
    row_positions = [i * stride_h for i in range(math.ceil((padded_h - overlap_aligned) / stride_h))]

    # Fix: recompute with the standard function so counts match.
    col_positions = compute_tile_positions(padded_w, tile_w, overlap_aligned)
    row_positions = compute_tile_positions(padded_h, tile_h, overlap_aligned)

    tiles = _build_tile_list(col_positions, row_positions, tile_w, tile_h)

    return TilePlan(
        strategy="padded",
        original_size=(image_w, image_h),
        tile_size=(tile_w, tile_h),
        overlap=(overlap_aligned, overlap_aligned),
        grid=(len(col_positions), len(row_positions)),
        divisible_by=divisible_by,
        padding=(pad_left, pad_top, pad_right, pad_bottom),
        tiles=tiles,
    )


def plan_auto(
    image_w: int,
    image_h: int,
    density: str = "balanced",
    divisible_by: int = 8,
) -> TilePlan:
    """Intelligent auto-tiling — pick tile size, overlap, and grid.

    ``density`` controls the trade-off between fewer/larger tiles (faster,
    more VRAM) and more/smaller tiles (slower, less VRAM):

    * ``"fewer tiles"`` — larger tiles (768), less overlap
    * ``"balanced"``    — middle ground (512 tiles, 12.5% overlap)
    * ``"more tiles"``  — smaller tiles (384), more overlap
    """
    presets = {
        "fewer tiles": (768, 0.08),
        "balanced":    (512, 0.125),
        "more tiles":  (384, 0.16),
    }
    base_size, overlap_ratio = presets.get(density, presets["balanced"])

    # Compute overlap.
    raw_overlap = int(base_size * overlap_ratio)
    overlap = max(divisible_by, _round_down(raw_overlap, divisible_by))

    tile_size = _round_up(base_size, divisible_by)

    # If the image is small enough, use a single tile.
    if image_w <= tile_size and image_h <= tile_size:
        single_w = _round_up(image_w, divisible_by)
        single_h = _round_up(image_h, divisible_by)
        return TilePlan(
            strategy="auto",
            original_size=(image_w, image_h),
            tile_size=(single_w, single_h),
            overlap=(0, 0),
            grid=(1, 1),
            divisible_by=divisible_by,
            tiles=[TileInfo(index=0, grid_pos=(0, 0), position=(0, 0),
                            size=(single_w, single_h))],
        )

    # Use uniform clamped placement with the computed parameters.
    plan = plan_uniform(image_w, image_h, tile_size, tile_size, overlap, divisible_by)
    plan.strategy = "auto"
    return plan
