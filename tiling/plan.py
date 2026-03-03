"""TilePlan and TileInfo — metadata describing a tiling layout.

The tiler produces a TilePlan that fully describes how tiles map back to the
original image.  The untiler consumes this plan to reconstruct the output.
Plans are transported between nodes as plain dicts (ComfyUI custom type
``TILE_PLAN``).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TileInfo:
    """Metadata for a single tile."""

    index: int
    grid_pos: tuple[int, int]     # (col, row)
    position: tuple[int, int]     # (x, y) top-left in original/padded image
    size: tuple[int, int]         # (width, height)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TileInfo:
        return cls(
            index=d["index"],
            grid_pos=tuple(d["grid_pos"]),
            position=tuple(d["position"]),
            size=tuple(d["size"]),
        )


@dataclass
class TilePlan:
    """Complete description of a tiling layout."""

    version: int = 1
    strategy: str = "uniform"
    original_size: tuple[int, int] = (0, 0)   # (width, height)
    tile_size: tuple[int, int] = (512, 512)    # (width, height)
    overlap: tuple[int, int] = (64, 64)        # (overlap_x, overlap_y)
    grid: tuple[int, int] = (1, 1)             # (cols, rows)
    divisible_by: int = 8
    padding: tuple[int, int, int, int] = (0, 0, 0, 0)  # (left, top, right, bottom)
    tiles: list[TileInfo] = field(default_factory=list)

    # ── serialisation ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "strategy": self.strategy,
            "original_size": list(self.original_size),
            "tile_size": list(self.tile_size),
            "overlap": list(self.overlap),
            "grid": list(self.grid),
            "divisible_by": self.divisible_by,
            "padding": list(self.padding),
            "tiles": [t.to_dict() for t in self.tiles],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TilePlan:
        return cls(
            version=d.get("version", 1),
            strategy=d["strategy"],
            original_size=tuple(d["original_size"]),
            tile_size=tuple(d["tile_size"]),
            overlap=tuple(d["overlap"]),
            grid=tuple(d["grid"]),
            divisible_by=d.get("divisible_by", 8),
            padding=tuple(d.get("padding", (0, 0, 0, 0))),
            tiles=[TileInfo.from_dict(t) for t in d.get("tiles", [])],
        )

    @property
    def tile_count(self) -> int:
        return len(self.tiles)

    @property
    def cols(self) -> int:
        return self.grid[0]

    @property
    def rows(self) -> int:
        return self.grid[1]
