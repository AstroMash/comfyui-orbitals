"""Ultimate Untiler — reassemble processed tiles into a single image.

Consumes a TILE_PLAN (from Ultimate Tiler) and the batch of processed tiles,
then merges them with weighted blending in overlap regions.

**Upscale-aware:**  If the incoming tiles are larger (or smaller) than the
plan's ``tile_size``, the untiler automatically detects the scale factor and
produces an output at the corresponding resolution.  This lets you drop an
upscaler (SeedVR2, Real-ESRGAN, …) between tiler and untiler without any
manual maths.
"""

from __future__ import annotations

import math
import numpy as np
import torch

from .tiling import TilePlan, TileInfo, create_weight_mask


class UltimateUntiler:
    """Reconstructs a full image from tiled pieces using weighted blending."""

    CATEGORY = "Orbitals/Tiling"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tiles": ("IMAGE",),
                "tile_plan": ("TILE_PLAN",),
            },
            "optional": {
                "blend_mode": (["cosine", "linear", "none"], {
                    "default": "cosine",
                    "tooltip": "Blending function for overlap regions.",
                }),
                "blend_strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "Ramp length as fraction of overlap (0 = hard cut, 1 = full ramp).",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "untile"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, tiles, **kwargs):
        # Hash tile content so ComfyUI re-executes when pixel data changes,
        # even if tensor shape is identical to the previous run.
        import hashlib
        h = hashlib.sha256(tiles.cpu().numpy().tobytes()[:65536]).hexdigest()
        return h

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _detect_scale(
        tiles: torch.Tensor,
        plan: TilePlan,
    ) -> tuple[float, float]:
        """Compare actual tile dimensions to the plan and return (sx, sy).

        Returns (1.0, 1.0) when no scaling occurred.
        """
        plan_tw, plan_th = plan.tile_size            # expected
        actual_th, actual_tw = tiles.shape[1:3]      # BHWC

        sx = actual_tw / plan_tw if plan_tw > 0 else 1.0
        sy = actual_th / plan_th if plan_th > 0 else 1.0
        return sx, sy

    @staticmethod
    def _scale_plan(plan: TilePlan, sx: float, sy: float) -> TilePlan:
        """Return a *new* TilePlan with every metric scaled by (sx, sy).

        Positions and sizes are rounded to the nearest integer.  The
        ``overlap`` is scaled and used for weight-mask generation so that
        blend ramps are proportional to the new tile size.
        """
        orig_w, orig_h = plan.original_size
        tile_w, tile_h = plan.tile_size
        ov_x, ov_y = plan.overlap
        pl, pt, pr, pb = plan.padding

        new_tiles = []
        for ti in plan.tiles:
            x, y = ti.position
            tw, th = ti.size
            new_tiles.append(TileInfo(
                index=ti.index,
                grid_pos=ti.grid_pos,
                position=(round(x * sx), round(y * sy)),
                size=(round(tw * sx), round(th * sy)),
            ))

        return TilePlan(
            version=plan.version,
            strategy=plan.strategy,
            original_size=(round(orig_w * sx), round(orig_h * sy)),
            tile_size=(round(tile_w * sx), round(tile_h * sy)),
            overlap=(round(ov_x * sx), round(ov_y * sy)),
            grid=plan.grid,
            divisible_by=plan.divisible_by,
            padding=(round(pl * sx), round(pt * sy),
                     round(pr * sx), round(pb * sy)),
            tiles=new_tiles,
        )

    # ── main entry ────────────────────────────────────────────────

    def untile(
        self,
        tiles: torch.Tensor,
        tile_plan: dict,
        blend_mode: str = "cosine",
        blend_strength: float = 1.0,
    ):
        plan = TilePlan.from_dict(tile_plan)

        # ── detect upscale / downscale ────────────────────────────
        sx, sy = self._detect_scale(tiles, plan)
        scaled = not (math.isclose(sx, 1.0, abs_tol=1e-4)
                      and math.isclose(sy, 1.0, abs_tol=1e-4))

        if scaled:
            plan = self._scale_plan(plan, sx, sy)
            print(f"[UltimateUntiler] Detected tile scale {sx:.4f}×{sy:.4f} "
                  f"→ output resolution {plan.original_size[0]}×{plan.original_size[1]}")

        orig_w, orig_h = plan.original_size
        tile_w, tile_h = plan.tile_size

        # Determine canvas size (padded if strategy == "padded").
        pl, pt, pr, pb = plan.padding
        canvas_w = orig_w + pl + pr
        canvas_h = orig_h + pt + pb

        # Unpack tiles from batch tensor.
        if tiles.dim() == 4:
            tile_list = [tiles[i] for i in range(tiles.shape[0])]
        elif tiles.dim() == 3:
            tile_list = [tiles]
        else:
            tile_list = [tiles]

        expected = plan.tile_count
        # Pad or trim tile list to match plan.
        if len(tile_list) > expected:
            tile_list = tile_list[:expected]
        while len(tile_list) < expected:
            if tile_list:
                tile_list.append(tile_list[-1].clone())
            else:
                tile_list.append(
                    torch.zeros((tile_h, tile_w, 3), dtype=torch.float32)
                )

        # Detect channel count from tiles.
        channels = tile_list[0].shape[-1] if tile_list else 3

        # ── weighted accumulation ────────────────────────────────
        result = np.zeros((canvas_h, canvas_w, channels), dtype=np.float64)
        weights = np.zeros((canvas_h, canvas_w), dtype=np.float64)

        for idx, ti in enumerate(plan.tiles):
            if idx >= len(tile_list):
                break

            tile_np = tile_list[idx].detach().cpu().numpy().astype(np.float64)
            tw, th = ti.size

            # Trim or pad tile data to the (possibly-scaled) declared size.
            actual_h, actual_w = tile_np.shape[:2]
            if actual_h > th or actual_w > tw:
                tile_np = tile_np[:th, :tw, :]
            elif actual_h < th or actual_w < tw:
                padded = np.zeros((th, tw, tile_np.shape[2]), dtype=np.float64)
                padded[:actual_h, :actual_w, :] = tile_np
                tile_np = padded

            x, y = ti.position
            x1 = min(x + tw, canvas_w)
            y1 = min(y + th, canvas_h)
            eff_w = x1 - x
            eff_h = y1 - y

            wmask = create_weight_mask(ti, plan, blend_mode, blend_strength)
            wmask = wmask[:eff_h, :eff_w]
            tile_region = tile_np[:eff_h, :eff_w, :]

            result[y:y1, x:x1, :] += tile_region * wmask[:, :, np.newaxis]
            weights[y:y1, x:x1] += wmask

        # Normalise.
        weights = np.maximum(weights, 1e-8)
        result = result / weights[:, :, np.newaxis]
        result = np.clip(result, 0.0, 1.0)

        # ── crop padding ─────────────────────────────────────────
        if any(p > 0 for p in plan.padding):
            result = result[pt:pt + orig_h, pl:pl + orig_w, :]

        out = torch.from_numpy(result.astype(np.float32)).unsqueeze(0)  # [1, H, W, C]
        return (out,)


NODE_CLASS_MAPPINGS = {
    "UltimateUntiler": UltimateUntiler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UltimateUntiler": "Ultimate Untiler",
}
