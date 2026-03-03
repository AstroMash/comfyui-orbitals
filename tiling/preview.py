"""Grid overlay preview — draws tile outlines on the input image.

The renderer uses PIL drawing so it has no heavy dependencies (matplotlib
etc.).  It produces an RGBA overlay composited onto the input.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .plan import TilePlan


# Palette for tile outlines — cycles through these.
_TILE_COLORS = [
    (66, 133, 244),   # blue
    (234, 67, 53),    # red
    (52, 168, 83),    # green
    (251, 188, 4),    # yellow
    (171, 71, 188),   # purple
    (0, 172, 193),    # teal
    (255, 112, 67),   # deep orange
    (121, 134, 203),  # indigo
]

_OVERLAP_FILL = (255, 255, 0, 30)  # subtle yellow tint for overlap regions
_BORDER_ALPHA = 180
_LABEL_COLOR = (255, 255, 255)
_LABEL_SHADOW = (0, 0, 0)


def render_tile_preview(
    image_np: np.ndarray,
    plan: TilePlan,
) -> np.ndarray:
    """Draw tile boundaries on *image_np* and return the composited result.

    Parameters
    ----------
    image_np:
        HWC uint8 numpy array (the original input image).
    plan:
        The computed tile plan.

    Returns
    -------
    numpy.ndarray
        HWC uint8 array with tile grid overlay.
    """
    h, w = image_np.shape[:2]
    base = Image.fromarray(image_np).convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    ov_x, ov_y = plan.overlap

    # Draw overlap shading first (lowest layer).
    for tile in plan.tiles:
        tx, ty = tile.position
        tw, th = tile.size
        col, row = tile.grid_pos

        # Left overlap region
        if col > 0 and ov_x > 0:
            x0 = tx
            x1 = min(tx + ov_x, tx + tw)
            draw.rectangle([x0, ty, x1, ty + th], fill=_OVERLAP_FILL)
        # Right overlap region
        if col < plan.cols - 1 and ov_x > 0:
            x0 = max(tx + tw - ov_x, tx)
            x1 = tx + tw
            draw.rectangle([x0, ty, x1, ty + th], fill=_OVERLAP_FILL)
        # Top overlap region
        if row > 0 and ov_y > 0:
            y0 = ty
            y1 = min(ty + ov_y, ty + th)
            draw.rectangle([tx, y0, tx + tw, y1], fill=_OVERLAP_FILL)
        # Bottom overlap region
        if row < plan.rows - 1 and ov_y > 0:
            y0 = max(ty + th - ov_y, ty)
            y1 = ty + th
            draw.rectangle([tx, y0, tx + tw, y1], fill=_OVERLAP_FILL)

    # Draw tile outlines.
    for tile in plan.tiles:
        tx, ty = tile.position
        tw, th = tile.size
        color_rgb = _TILE_COLORS[tile.index % len(_TILE_COLORS)]
        outline_color = (*color_rgb, _BORDER_ALPHA)
        # 2px rectangle outline
        draw.rectangle([tx, ty, tx + tw - 1, ty + th - 1], outline=outline_color, width=2)

    # Draw tile index labels at tile centres.
    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, min(tw, th) // 8))
    except (OSError, IOError):
        font = ImageFont.load_default()

    for tile in plan.tiles:
        tx, ty = tile.position
        tw, th = tile.size
        label = str(tile.index)
        cx = tx + tw // 2
        cy = ty + th // 2
        bbox = font.getbbox(label)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        lx = cx - lw // 2
        ly = cy - lh // 2
        # Shadow
        draw.text((lx + 1, ly + 1), label, fill=(*_LABEL_SHADOW, 200), font=font)
        # Label
        draw.text((lx, ly), label, fill=(*_LABEL_COLOR, 240), font=font)

    # Draw summary text at top-left.
    cols, rows = plan.grid
    tw, th = plan.tile_size
    summary = (
        f"{plan.strategy}  |  {cols}x{rows} grid  |  "
        f"tile {tw}x{th}  |  overlap {ov_x},{ov_y}  |  "
        f"{plan.tile_count} tiles"
    )
    try:
        sfont = ImageFont.truetype("arial.ttf", size=13)
    except (OSError, IOError):
        sfont = ImageFont.load_default()

    # Background bar for readability.
    sb = sfont.getbbox(summary)
    sw = sb[2] - sb[0] + 12
    sh = sb[3] - sb[1] + 8
    draw.rectangle([0, 0, sw, sh], fill=(0, 0, 0, 180))
    draw.text((6, 3), summary, fill=(255, 255, 255, 240), font=sfont)

    composited = Image.alpha_composite(base, overlay).convert("RGB")
    return np.array(composited, dtype=np.uint8)
