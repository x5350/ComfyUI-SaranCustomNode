import os
import fnmatch
from PIL import Image, ImageOps
import torch
import numpy as np
from numpy.f2py.f2py2e import filter_files


class SaranFileBrowser:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"default": "",
                                         "multiline": False,
                                         "tooltip": "absolute or relative path (ex: ComfyUI/output/1_prompt)"}),
                "extension": ("STRING", {"default": ".txt"}),
                "file_filter": ("STRING", {"default": "*",
                                           "tooltip": "ex: ZIT_*, Flux_*, "}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_list_text",)
    FUNCTION = "browse_files"
    CATEGORY = "SaranCustomNode"

    def browse_files(self, directory, extension, file_filter):
        if not directory or not os.path.exists(directory):
            return ("",)

        ext = extension.strip()
        if ext and not ext.startswith("."):
            ext = "." + ext

        matched_files = []
        if file_filter and file_filter != "*":
            if not file_filter.endswith(ext):
                file_filter = file_filter + ext
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if ext and not file.endswith(ext):
                        continue
                    if file_filter and file_filter != "*":
                        if not fnmatch.fnmatch(file, file_filter):
                            continue
                    matched_files.append(file)
        except Exception as e:
            print(f"[SaranFileBrowser] Error: {e}")

        matched_files = sorted(list(set(matched_files)))
        result = "\n".join(matched_files)
        return (result,)

class SaranSubstring:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": False}),
                "skip_count": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "direction": (["from_start", "from_end"],),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("modified_string",)
    FUNCTION = "process_substring"
    CATEGORY = "SaranCustomNode"

    def process_substring(self, text, skip_count, direction):
        if not text:
            return ("",)

        if direction == "from_start":
            if skip_count >= len(text):
                return ("",)
            result = text[skip_count:]
        else:  # from_end
            if skip_count >= len(text):
                return ("",)
            result = text[:-skip_count] if skip_count > 0 else text

        return (result,)

class SaranLoadImageFromPath:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"default": "", "multiline": False}),
                "file_name": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load_image"
    CATEGORY = "SaranCustomNode"

    def load_image(self, directory, file_name):
        if not directory or not file_name:
            raise ValueError("Directory and file name must be provided.")

        # Clean up path formatting
        full_path = os.path.join(directory.strip(), file_name.strip())
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Image not found at: {full_path}")

        img = Image.open(full_path)
        img = ImageOps.exif_transpose(img)

        if img.mode == 'I':
            img = img.point(lambda i: i * (1 / 255))
        image = img.convert("RGB")

        image_np = np.array(image).astype(np.float32) / 2.55 / 100.0  # equivalent to / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]

        if 'A' in img.getbands():
            mask = np.array(img.getchannel('A')).astype(np.float32) / 255.0
            mask = 1.0 - torch.from_numpy(mask)
        else:
            mask = torch.zeros((image_tensor.shape[1], image_tensor.shape[2]), dtype=torch.float32)

        return (image_tensor, mask)

NODE_CLASS_MAPPINGS = {
    "SaranFileBrowser": SaranFileBrowser,
    "SaranSubstring": SaranSubstring,
    "SaranLoadImageFromPath": SaranLoadImageFromPath,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaranFileBrowser": "Directory File Browser (Saran)",
    "SaranSubstring": "Substring (Saran)",
    "SaranLoadImageFromPath": "Load Image From Path (Saran)",
}
