# Orbitals for ComfyUI

A collection of custom nodes for ComfyUI workflows.

## Nodes Included

### 🏷️ Taggregator

A dynamic tag management node that allows you to organize your prompts into multiple categories with individual weights and enable/disable toggles.

**Features:**

- Organize prompts into labeled categories
- Individual weight control per category (0.0 - 2.0)
- Enable/disable categories on the fly
- Clean, intuitive UI with add/remove functionality
- Proper weight formatting for Stable Diffusion prompts

**Usage:**

1. Add the Taggregator node to your workflow
2. The base prompt is always visible at the top
3. Click "+ Add Category" to create new tag groups
4. Enter a label for each category (e.g., "Style", "Lighting", "Details")
5. Add your tags in the text area
6. Adjust the weight slider (1.0 is neutral)
7. Toggle the checkbox to enable/disable categories
8. Remove categories with the × button

**Output Format:**
Enabled categories are combined with proper weighting:

- Weight 1.0: tags appear as-is
- Other weights: tags appear as `(tags:1.2)` format

### 🌐 gcLatentTunnel

Garbage collection "tunnel" node that forces memory cleanup after latent passes through it. Useful for managing VRAM in complex workflows.

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
