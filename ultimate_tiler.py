"""Ultimate Tiler — split an image into uniform, well-planned tiles.

Strategies:
  auto     — pick tile size / overlap / grid automatically
  uniform  — fixed tile size, clamped-to-bounds placement (no slivers)
  grid     — user specifies rows/cols, tile size derived
  padded   — pad image so grid divides cleanly

Upscale target:
  Set ``upscale_mode`` to tell the tiler what final resolution you want.
  It computes two per-tile resolution values:

  - ``upscaler_resolution``     → shortest edge of upscaled tile
                                   (wire to SeedVR2 ``resolution``)
  - ``upscaler_max_resolution`` → longest edge of upscaled tile
                                   (wire to SeedVR2 ``max_resolution``)
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

from .tiling import (
    TilePlan,
    plan_auto,
    plan_uniform,
    plan_grid,
    plan_padded,
    render_tile_preview,
)


class UltimateTiler:
    """Splits an input IMAGE into a batch of uniform tiles + metadata."""

    CATEGORY = "Orbitals/Tiling"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strategy": (["auto", "uniform", "grid", "padded"],),
            },
            "optional": {
                "tile_width": ("INT", {
                    "default": 512, "min": 64, "max": 4096, "step": 8,
                    "tooltip": "Tile width in pixels (uniform/padded modes).",
                }),
                "tile_height": ("INT", {
                    "default": 512, "min": 64, "max": 4096, "step": 8,
                    "tooltip": "Tile height in pixels (uniform/padded modes).",
                }),
                "overlap": ("INT", {
                    "default": 64, "min": 0, "max": 512, "step": 8,
                    "tooltip": "Overlap between adjacent tiles in pixels.",
                }),
                "rows": ("INT", {
                    "default": 2, "min": 1, "max": 32, "step": 1,
                    "tooltip": "Number of rows (grid mode only).",
                }),
                "cols": ("INT", {
                    "default": 2, "min": 1, "max": 32, "step": 1,
                    "tooltip": "Number of columns (grid mode only).",
                }),
                "divisible_by": ("INT", {
                    "default": 8, "min": 1, "max": 64, "step": 1,
                    "tooltip": "Tile dimensions will be rounded to multiples of this.",
                }),
                "pad_mode": (["reflect", "replicate", "constant"], {
                    "default": "reflect",
                    "tooltip": "Padding mode for the padded strategy.",
                }),
                "density": (["fewer tiles", "balanced", "more tiles"], {
                    "default": "balanced",
                    "tooltip": "Auto mode tile density: fewer tiles = larger 768px tiles, more tiles = smaller 384px tiles.",
                }),
                "upscale_mode": (["none", "scale", "fit to"], {
                    "default": "none",
                    "tooltip": (
                        "How to compute the upscaler target. "
                        "'scale' = multiply by upscale_factor. "
                        "'fit to' = resize longest edge to upscale_target."
                    ),
                }),
                "upscale_factor": ("FLOAT", {
                    "default": 2.0, "min": 0.5, "max": 8.0, "step": 0.25,
                    "tooltip": "Scale multiplier for the final image (scale mode). 2.0 = double size.",
                }),
                "upscale_target": ("INT", {
                    "default": 3840, "min": 64, "max": 16384, "step": 8,
                    "tooltip": "Target for the longest edge of the final image, in pixels (fit to mode).",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "TILE_PLAN", "IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("tiles", "tile_plan", "preview", "tile_count",
                    "upscaler_resolution", "upscaler_max_resolution")
    FUNCTION = "tile"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, image, **kwargs):
        # Hash image content so ComfyUI re-executes when pixels change,
        # even if shape/dtype are identical to the previous run.
        import hashlib
        h = hashlib.sha256(image.cpu().numpy().tobytes()[:65536]).hexdigest()
        return h

    def tile(
        self,
        image: torch.Tensor,
        strategy: str,
        tile_width: int = 512,
        tile_height: int = 512,
        overlap: int = 64,
        rows: int = 2,
        cols: int = 2,
        divisible_by: int = 8,
        pad_mode: str = "reflect",
        density: str = "balanced",
        upscale_mode: str = "none",
        upscale_factor: float = 2.0,
        upscale_target: int = 3840,
    ):
        # Use first image in batch if multiple provided.
        if image.shape[0] > 1:
            image = image[:1]

        _, img_h, img_w, channels = image.shape

        # ── compute tile plan ────────────────────────────────────
        if strategy == "auto":
            plan = plan_auto(img_w, img_h, density=density, divisible_by=divisible_by)
        elif strategy == "uniform":
            plan = plan_uniform(img_w, img_h, tile_width, tile_height, overlap, divisible_by)
        elif strategy == "grid":
            plan = plan_grid(img_w, img_h, rows, cols, overlap, divisible_by)
        elif strategy == "padded":
            plan = plan_padded(img_w, img_h, tile_width, tile_height, overlap, divisible_by, pad_mode)
        else:
            raise ValueError(f"Unknown tiling strategy: {strategy}")

        # ── compute upscaler target per tile ──────────────────────
        tile_w, tile_h = plan.tile_size
        tile_short = min(tile_w, tile_h)
        tile_long = max(tile_w, tile_h)

        if upscale_mode == "scale":
            scale = max(0.5, upscale_factor)
            upscaler_res = max(64, round(tile_short * scale))
            upscaler_max = max(64, round(tile_long * scale))
            print(f"[UltimateTiler] Upscale {scale:.2f}× "
                  f"→ {img_w}×{img_h} becomes ~{round(img_w * scale)}×{round(img_h * scale)}, "
                  f"upscaler: resolution={upscaler_res}, max_resolution={upscaler_max}")
        elif upscale_mode == "fit to":
            longest = max(img_w, img_h)
            scale = upscale_target / longest if longest > 0 else 1.0
            upscaler_res = max(64, round(tile_short * scale))
            upscaler_max = max(64, round(tile_long * scale))
            out_w, out_h = round(img_w * scale), round(img_h * scale)
            print(f"[UltimateTiler] Fit longest edge to {upscale_target}px (scale {scale:.3f}×) "
                  f"→ {img_w}×{img_h} becomes ~{out_w}×{out_h}, "
                  f"upscaler: resolution={upscaler_res}, max_resolution={upscaler_max}")
        else:
            # "none" — output the input tile size (passthrough / no upscale).
            upscaler_res = tile_short
            upscaler_max = tile_long

        # ── apply padding if needed ──────────────────────────────
        work_image = image[0]  # [H, W, C]

        if strategy == "padded" and any(p > 0 for p in plan.padding):
            pl, pt, pr, pb = plan.padding
            # F.pad expects [C, H, W] and pad order is (left, right, top, bottom)
            img_chw = work_image.permute(2, 0, 1)  # [C, H, W]
            torch_pad_mode = pad_mode if pad_mode != "constant" else "constant"
            img_chw = F.pad(img_chw, (pl, pr, pt, pb), mode=torch_pad_mode, value=0)
            work_image = img_chw.permute(1, 2, 0)  # [H, W, C]

        padded_h, padded_w = work_image.shape[:2]

        # ── slice tiles ──────────────────────────────────────────
        tiles_list: list[torch.Tensor] = []

        for ti in plan.tiles:
            x, y = ti.position
            tw, th = ti.size

            # Clamp extraction region to padded image bounds.
            x1 = min(x + tw, padded_w)
            y1 = min(y + th, padded_h)
            crop = work_image[y:y1, x:x1, :]  # [crop_h, crop_w, C]

            # Pad if crop is smaller than tile size (shouldn't happen in
            # clamped mode, but defensive).
            crop_h, crop_w = crop.shape[:2]
            if crop_h < th or crop_w < tw:
                padded_tile = torch.zeros((th, tw, channels), dtype=image.dtype, device=image.device)
                padded_tile[:crop_h, :crop_w, :] = crop
                crop = padded_tile

            tiles_list.append(crop.unsqueeze(0))  # [1, H, W, C]

        tiles_batch = torch.cat(tiles_list, dim=0)  # [N, H, W, C]

        # ── preview image ────────────────────────────────────────
        # For padded strategy, draw preview on the padded canvas so tile
        # positions (which are in padded-space coords) line up correctly.
        if strategy == "padded" and any(p > 0 for p in plan.padding):
            preview_src = work_image
        else:
            preview_src = image[0]
        preview_np = (preview_src.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        preview_np = render_tile_preview(preview_np, plan)
        preview_tensor = torch.from_numpy(preview_np.astype(np.float32) / 255.0).unsqueeze(0)

        # ── serialise plan ───────────────────────────────────────
        plan_dict = plan.to_dict()
        tile_count = len(plan.tiles)

        return (tiles_batch, plan_dict, preview_tensor, tile_count,
                upscaler_res, upscaler_max)


NODE_CLASS_MAPPINGS = {
    "UltimateTiler": UltimateTiler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UltimateTiler": "Ultimate Tiler",
}
