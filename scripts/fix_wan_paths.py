import json, sys

with open("/root/ComfyUI/user/default/workflows/wan22_i2v_kijai.json", "r") as f:
    wf = json.load(f)

fixed = 0
for n in wf["nodes"]:
    wv = n.get("widgets_values", [])
    for i, v in enumerate(wv):
        if isinstance(v, str) and ".safetensors" in v:
            old = v
            # Normalize all slashes and take just filename
            clean = v.replace("\\", "/")
            if "/" in clean:
                clean = clean.rsplit("/", 1)[-1]
            if clean != old:
                n["widgets_values"][i] = clean
                fixed += 1
                print(f"Fixed: {repr(old)} -> {clean}")

print(f"Total fixes: {fixed}")

with open("/root/ComfyUI/user/default/workflows/wan22_i2v_kijai.json", "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
print("Saved")
