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
