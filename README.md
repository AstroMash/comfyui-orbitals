# 💫 Orbitals for ComfyUI

A collection of custom nodes for ComfyUI workflows.

## Nodes Included

### 🏷️ Taggregator

A dynamic tag management node that allows you to organize your prompts into multiple categories with individual enable/disable toggles.

**Features:**

- Organize prompts into labeled categories
- Enable/disable categories on the fly
- Clean, intuitive UI with add/remove functionality

**Usage:**

1. Add the Taggregator node to your workflow
2. The base prompt is always visible at the top
3. Click "+ Add Category" to create new tag groups
4. Enter a label for each category (e.g., "Style", "Lighting", "Details")
5. Add your tags in the text area (natural language works too)
6. Toggle the checkbox to enable/disable categories
7. Remove categories with the × button

### 🌐 Latent Garbage Collector

Garbage collection "tunnel" node that forces memory cleanup after latent passes through it. Useful for managing VRAM in complex workflows.

### 🔤 CLIP Encode (From String)

Encodes text prompts directly from a string input. Useful for encoding strings from other nodes (like Taggregator) into conditioning.

### 🎯 Select (Index)

Deterministic, index-based selection from a user-defined list. Selects a value from a comma-separated list using a zero-based index. Returns the selected value, its index, and the original options string.

### 🔲 Ultimate Tiler

Splits an image into a batch of uniformly-sized tiles with optional overlap. Outputs the tile batch, a `TILE_PLAN` metadata object, a preview image, and upscaler resolution hints for use with upscalers like SeedVR2.

**Strategies:**

- `auto` — automatically picks tile size, overlap, and grid based on image size and a density setting (fewer/balanced/more tiles)
- `uniform` — fixed tile size with configurable overlap; tiles are clamped to image bounds (no slivers)
- `grid` — specify rows and columns; tile size is derived from the image dimensions
- `padded` — pads the image so the grid divides cleanly; supports reflect, replicate, or constant padding

**Upscale target outputs:**

Set `upscale_mode` to compute per-tile resolution hints:

- `scale` — multiply tile dimensions by `upscale_factor`
- `fit to` — scale so the longest edge of the final image hits `upscale_target` pixels
- `none` — outputs the raw tile size (passthrough)

The `upscaler_resolution` and `upscaler_max_resolution` outputs wire directly to SeedVR2's `resolution` and `max_resolution` inputs.

### 🧩 Ultimate Untiler

Reassembles a batch of processed tiles back into a single image using weighted blending in overlap regions. Consumes the `TILE_PLAN` from Ultimate Tiler.

**Upscale-aware:** if the incoming tiles are larger (or smaller) than the original plan's tile size, the untiler automatically detects the scale factor and produces the output at the correct resolution — no manual configuration needed.

**Blend options:**

- `blend_mode` — `cosine` (smooth), `linear`, or `none` (hard cut)
- `blend_strength` — ramp length as a fraction of the overlap (0 = hard cut, 1 = full ramp)

## Installation

1. Open a terminal and navigate to your ComfyUI `custom_nodes` directory and clone the Orbitals repository:

   ```bash
   git clone https://github.com/AstroMash/comfyui-orbitals.git
   ```

2. Restart ComfyUI to load the new nodes.

## Troubleshooting

**Node doesn't appear in ComfyUI:**

1. Make sure you've restarted ComfyUI completely
2. Check the console for any error messages
3. Verify the file structure matches this repo

**Custom UI not loading:**

1. Hard refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)
2. Clear browser cache
3. Check browser console (F12) for JavaScript errors

## Development

PRs and Issues are welcome. If you have ideas for new nodes or improvements, feel free to contribute!
