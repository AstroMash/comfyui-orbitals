import torch
import gc

class LatentGarbageCollector:
    """
    Latent Garbage Collector - Forces memory cleanup after latent passes through
    Useful for managing VRAM in large workflows
    """
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "samples": ("LATENT",),
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "gcTunnel"
    CATEGORY = "Orbitals"

    def gcTunnel(self, samples):
        s = samples.copy()
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        return (s,)

NODE_CLASS_MAPPINGS = {
    "LatentGarbageCollector": LatentGarbageCollector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LatentGarbageCollector": "🗑️ Latent Garbage Collector"
}
