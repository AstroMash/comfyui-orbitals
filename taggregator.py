"""
Taggregator - Multi-Tag Prompt Combiner
A dynamic UI node for organizing prompts into categories with enable/disable toggles
"""

import json


class Taggregator:
    """
    Combines multiple prompt categories into a single output string.
    Features a custom UI with:
    - Base prompt section
    - Multiple tag categories with labels
    - Enable/disable toggles for each section
    - Drag-to-reorder functionality
    """
    
    CATEGORY = "Orbitals"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_items_json": ("STRING", {
                    "default": "[]",
                    "multiline": True,
                    "forceInput": False,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "combine_prompts"
    OUTPUT_NODE = True

    def combine_prompts(self, prompt_items_json):
        try:
            items = json.loads(prompt_items_json)
        except Exception:
            items = []
        
        combined = []
        for item in items:
            if item.get("type") == "base":
                # Base prompt
                if item.get("enabled", True) and item.get("text", "").strip():
                    combined.append(item["text"].strip())
            elif item.get("type") == "category":
                # Category
                if item.get("enabled", True) and item.get("tags", "").strip():
                    combined.append(item["tags"].strip())
        
        return (", ".join(combined),)


NODE_CLASS_MAPPINGS = {
    "Taggregator": Taggregator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Taggregator": "🏷️ Taggregator"
}
