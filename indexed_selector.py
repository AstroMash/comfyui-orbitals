"""
Indexed Selector Node for ComfyUI
Deterministic, index-based selection from a user-defined list.
"""

class IndexedSelector:
    """
    Selects a value from a comma-separated list using a zero-based index.
    Returns the selected value, its index, and the original options string.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "options": ("STRING", {
                    "default": "Option A,Option B,Option C",
                    "multiline": False,
                    "tooltip": "Comma-separated list of options"
                }),
                "selected": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1,
                    "tooltip": "Zero-based index of selected option"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "STRING",)
    RETURN_NAMES = ("value", "index", "all_options",)
    FUNCTION = "select_option"
    CATEGORY = "Orbitals"
    OUTPUT_NODE = False

    def select_option(self, options, selected):
        """
        Parses comma-separated options and returns the selected entry.
        """

        # Parse options
        options_list = [opt.strip() for opt in options.split(",") if opt.strip()]

        # Handle empty list
        if not options_list:
            return ("", 0, "")

        # Clamp selection to valid range
        selected_index = max(0, min(selected, len(options_list) - 1))
        selected_value = options_list[selected_index]

        return (selected_value, selected_index, options)


# Node registration
NODE_CLASS_MAPPINGS = {
    "IndexedSelector": IndexedSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexedSelector": "🎯 Select (Index)",
}