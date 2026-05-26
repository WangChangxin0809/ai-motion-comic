"""Build and test FLUX workflow on remote ComfyUI server."""
import json
import urllib.request
import uuid
import time
import sys

# ============================================================
# Step 1: Build workflow JSON with full input/output metadata
# ============================================================

workflow = {
    "version": 1,
    "state": {},
    "last_node_id": 13,
    "last_link_id": 13,
    "nodes": [
        {
            "id": 1, "type": "UNETLoader", "pos": [50, 100], "size": [300, 100],
            "flags": {}, "order": 0, "mode": 0,
            "inputs": [
                {"name": "unet_name", "type": "COMBO", "widget": {"name": "unet_name"}, "link": None},
                {"name": "weight_dtype", "type": "COMBO", "widget": {"name": "weight_dtype"}, "link": None},
            ],
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [1, 2]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "UNETLoader"},
            "widgets_values": ["FLUX1/flux1-dev-fp8.safetensors", "default"]
        },
        {
            "id": 2, "type": "DualCLIPLoader", "pos": [50, 250], "size": [300, 120],
            "flags": {}, "order": 1, "mode": 0,
            "inputs": [
                {"name": "clip_name1", "type": "COMBO", "widget": {"name": "clip_name1"}, "link": None},
                {"name": "clip_name2", "type": "COMBO", "widget": {"name": "clip_name2"}, "link": None},
                {"name": "type", "type": "COMBO", "widget": {"name": "type"}, "link": None},
            ],
            "outputs": [
                {"name": "CLIP", "type": "CLIP", "links": [3]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "DualCLIPLoader"},
            "widgets_values": ["clip_l.safetensors", "t5/t5xxl_fp8_e4m3fn.safetensors", "flux"]
        },
        {
            "id": 3, "type": "VAELoader", "pos": [50, 430], "size": [300, 80],
            "flags": {}, "order": 2, "mode": 0,
            "inputs": [
                {"name": "vae_name", "type": "COMBO", "widget": {"name": "vae_name"}, "link": None},
            ],
            "outputs": [
                {"name": "VAE", "type": "VAE", "links": [4]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "VAELoader"},
            "widgets_values": ["FLUX1/ae.safetensors"]
        },
        {
            "id": 4, "type": "CLIPTextEncode", "pos": [400, 250], "size": [450, 160],
            "flags": {}, "order": 3, "mode": 0, "title": "Positive Prompt",
            "inputs": [
                {"name": "text", "type": "STRING", "widget": {"name": "text"}, "link": None},
                {"name": "clip", "type": "CLIP", "link": 3},
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [5]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "CLIPTextEncode"},
            "widgets_values": ["a cat sitting on a wooden table, warm afternoon light, photorealistic"]
        },
        {
            "id": 5, "type": "EmptyLatentImage", "pos": [400, 480], "size": [300, 100],
            "flags": {}, "order": 4, "mode": 0,
            "inputs": [
                {"name": "width", "type": "INT", "widget": {"name": "width"}, "link": None},
                {"name": "height", "type": "INT", "widget": {"name": "height"}, "link": None},
                {"name": "batch_size", "type": "INT", "widget": {"name": "batch_size"}, "link": None},
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [6]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "EmptyLatentImage"},
            "widgets_values": [1024, 1024, 1]
        },
        {
            "id": 6, "type": "RandomNoise", "pos": [900, 100], "size": [300, 80],
            "flags": {}, "order": 5, "mode": 0,
            "inputs": [
                {"name": "noise_seed", "type": "INT", "widget": {"name": "noise_seed"}, "link": None},
            ],
            "outputs": [
                {"name": "NOISE", "type": "NOISE", "links": [7]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "RandomNoise"},
            "widgets_values": [42]
        },
        {
            "id": 7, "type": "FluxGuidance", "pos": [400, 620], "size": [300, 80],
            "flags": {}, "order": 6, "mode": 0,
            "inputs": [
                {"name": "conditioning", "type": "CONDITIONING", "link": 5},
                {"name": "guidance", "type": "FLOAT", "widget": {"name": "guidance"}, "link": None},
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [8]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "FluxGuidance"},
            "widgets_values": [3.5]
        },
        {
            "id": 8, "type": "BasicGuider", "pos": [750, 250], "size": [300, 80],
            "flags": {}, "order": 7, "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "conditioning", "type": "CONDITIONING", "link": 8},
            ],
            "outputs": [
                {"name": "GUIDER", "type": "GUIDER", "links": [9]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "BasicGuider"},
            "widgets_values": []
        },
        {
            "id": 9, "type": "BasicScheduler", "pos": [750, 420], "size": [300, 100],
            "flags": {}, "order": 8, "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 2},
                {"name": "scheduler", "type": "COMBO", "widget": {"name": "scheduler"}, "link": None},
                {"name": "steps", "type": "INT", "widget": {"name": "steps"}, "link": None},
                {"name": "denoise", "type": "FLOAT", "widget": {"name": "denoise"}, "link": None},
            ],
            "outputs": [
                {"name": "SIGMAS", "type": "SIGMAS", "links": [10]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "BasicScheduler"},
            "widgets_values": ["simple", 20, 1.0]
        },
        {
            "id": 10, "type": "KSamplerSelect", "pos": [750, 580], "size": [300, 80],
            "flags": {}, "order": 9, "mode": 0,
            "inputs": [
                {"name": "sampler_name", "type": "COMBO", "widget": {"name": "sampler_name"}, "link": None},
            ],
            "outputs": [
                {"name": "SAMPLER", "type": "SAMPLER", "links": [11]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "KSamplerSelect"},
            "widgets_values": ["euler"]
        },
        {
            "id": 11, "type": "SamplerCustomAdvanced", "pos": [1100, 350], "size": [320, 130],
            "flags": {}, "order": 10, "mode": 0,
            "inputs": [
                {"name": "noise", "type": "NOISE", "link": 7},
                {"name": "guider", "type": "GUIDER", "link": 9},
                {"name": "sampler", "type": "SAMPLER", "link": 11},
                {"name": "sigmas", "type": "SIGMAS", "link": 10},
                {"name": "latent_image", "type": "LATENT", "link": 6},
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [12]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "SamplerCustomAdvanced"},
            "widgets_values": []
        },
        {
            "id": 12, "type": "VAEDecode", "pos": [1450, 350], "size": [300, 80],
            "flags": {}, "order": 11, "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 12},
                {"name": "vae", "type": "VAE", "link": 4},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [13]},
            ],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "VAEDecode"},
            "widgets_values": []
        },
        {
            "id": 13, "type": "SaveImage", "pos": [1450, 500], "size": [300, 100],
            "flags": {}, "order": 12, "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 13},
                {"name": "filename_prefix", "type": "STRING", "widget": {"name": "filename_prefix"}, "link": None},
            ],
            "outputs": [],
            "properties": {"cnr_id": "comfy-core", "Node name for S&R": "SaveImage"},
            "widgets_values": ["Flux"]
        },
    ],
    "links": [
        [1, 1, 0, 8, 0, "MODEL"],
        [2, 1, 0, 9, 0, "MODEL"],
        [3, 2, 0, 4, 1, "CLIP"],
        [4, 3, 0, 12, 1, "VAE"],
        [5, 4, 0, 7, 0, "CONDITIONING"],
        [6, 5, 0, 11, 4, "LATENT"],
        [7, 6, 0, 11, 0, "NOISE"],
        [8, 7, 0, 8, 1, "CONDITIONING"],
        [9, 8, 0, 11, 1, "GUIDER"],
        [10, 9, 0, 11, 3, "SIGMAS"],
        [11, 10, 0, 11, 2, "SAMPLER"],
        [12, 11, 0, 12, 0, "LATENT"],
        [13, 12, 0, 13, 0, "IMAGE"],
    ],
    "groups": [],
    "config": {},
    "extra": {}
}

# Save workflow file
with open("/root/ComfyUI/user/default/workflows/flux_txt2img.json", "w") as f:
    json.dump(workflow, f, indent=2)
print("Step 1: Workflow file saved")

# ============================================================
# Step 2: Build API prompt from workflow
# ============================================================
api_prompt = {
    "1": {"inputs": {"unet_name": "FLUX1/flux1-dev-fp8.safetensors", "weight_dtype": "default"}, "class_type": "UNETLoader"},
    "2": {"inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5/t5xxl_fp8_e4m3fn.safetensors", "type": "flux"}, "class_type": "DualCLIPLoader"},
    "3": {"inputs": {"vae_name": "FLUX1/ae.safetensors"}, "class_type": "VAELoader"},
    "4": {"inputs": {"text": "a cat sitting on a wooden table, warm afternoon light, photorealistic", "clip": ["2", 0]}, "class_type": "CLIPTextEncode"},
    "5": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
    "6": {"inputs": {"noise_seed": 42}, "class_type": "RandomNoise"},
    "7": {"inputs": {"conditioning": ["4", 0], "guidance": 3.5}, "class_type": "FluxGuidance"},
    "8": {"inputs": {"model": ["1", 0], "conditioning": ["7", 0]}, "class_type": "BasicGuider"},
    "9": {"inputs": {"model": ["1", 0], "scheduler": "simple", "steps": 20, "denoise": 1.0}, "class_type": "BasicScheduler"},
    "10": {"inputs": {"sampler_name": "euler"}, "class_type": "KSamplerSelect"},
    "11": {"inputs": {"noise": ["6", 0], "guider": ["8", 0], "sampler": ["10", 0], "sigmas": ["9", 0], "latent_image": ["5", 0]}, "class_type": "SamplerCustomAdvanced"},
    "12": {"inputs": {"samples": ["11", 0], "vae": ["3", 0]}, "class_type": "VAEDecode"},
    "13": {"inputs": {"images": ["12", 0], "filename_prefix": "Flux"}, "class_type": "SaveImage"},
}

# ============================================================
# Step 3: Submit to ComfyUI API
# ============================================================
body = json.dumps({"prompt": api_prompt, "client_id": "flux-test"}).encode()
req = urllib.request.Request("http://127.0.0.1:8188/api/prompt", data=body)
resp = json.loads(urllib.request.urlopen(req).read())

print(f"Step 2: Submitted, node_errors={resp.get('node_errors', {})}")
pid = resp["prompt_id"]

# ============================================================
# Step 4: Wait for completion
# ============================================================
for i in range(40):
    time.sleep(5)
    try:
        hdata = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/api/history/{pid}").read())
    except:
        continue
    if pid in hdata:
        status = hdata[pid]["status"]["status_str"]
        completed = hdata[pid]["status"]["completed"]
        print(f"  [{i*5}s] {status}")
        if completed:
            for nid, out in hdata[pid]["outputs"].items():
                for img in out.get("images", []):
                    fn = img["filename"]
                    sf = img.get("subfolder", "")
                    path = f"/root/ComfyUI/output/{sf}/{fn}" if sf else f"/root/ComfyUI/output/{fn}"
                    print(f"Step 3: SUCCESS - {path}")
            break
    else:
        print(f"  [{i*5}s] waiting...")
else:
    print("Step 3: TIMEOUT")

print("DONE")
