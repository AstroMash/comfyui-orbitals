"""
CLIP Encode From String - Encodes a string input with CLIP
Useful for encoding strings from other nodes (like Taggregator) into conditioning
"""


class CLIPEncodeFromString:
    """
    Takes a STRING input from another node and encodes it with CLIP.
    Unlike the standard CLIP Text Encode, this accepts strings from node connections
    rather than having a text input box.
    """
    
    CATEGORY = "Orbitals"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "string": ("STRING", {
                    "multiline": True,
                    "forceInput": True,
                }),
            },
        }

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"

    def encode(self, clip, string):
        tokens = clip.tokenize(string)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        return ([[cond, {"pooled_output": pooled}]],)


NODE_CLASS_MAPPINGS = {
    "CLIPEncodeFromString": CLIPEncodeFromString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPEncodeFromString": "🔤 CLIP Encode (From String)"
}
