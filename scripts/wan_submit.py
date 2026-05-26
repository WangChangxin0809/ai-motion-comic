"""Build and submit Wan I2V API prompt from workflow JSON."""
import json, urllib.request, sys, time

WF_PATH = "/root/ComfyUI/user/default/workflows/wan22_i2v_kijai.json"
IMAGE = "AnimeShrine_00001_.png"
PROMPT = "the shrine maiden slowly turns her head toward the camera and smiles gently, cherry blossom petals drifting across the scene, her black ponytail swaying softly in the breeze, warm sunset light flickering through the torii gate, cinematic slow motion"

with open(WF_PATH) as f:
    wf = json.load(f)

# Build link map: (to_node_id, to_slot) -> [from_node_str, from_slot]
link_map = {}
for link in wf["links"]:
    lid, fn, fs, tn, ts, ltype = link
    link_map[(str(tn), ts)] = [str(fn), fs]

# Build API prompt
api = {}
for node in wf["nodes"]:
    nid = str(node["id"])
    inputs = {}
    node_inputs = node.get("inputs", [])
    wv = list(node.get("widgets_values", []))

    for si, inp in enumerate(node_inputs):
        key = (nid, si)
        if key in link_map:
            inputs[inp["name"]] = link_map[key]
        elif wv:
            inputs[inp["name"]] = wv.pop(0)

    api[nid] = {"inputs": inputs, "class_type": node["type"]}

# Override image and prompt
for nid, nd in api.items():
    if nd["class_type"] == "LoadImage":
        nd["inputs"]["image"] = IMAGE
    if nd["class_type"] == "WanVideoTextEncode":
        nd["inputs"]["prompt"] = PROMPT

# Submit
body = json.dumps({"prompt": api}).encode()
req = urllib.request.Request("http://127.0.0.1:8188/api/prompt", data=body)
resp = json.loads(urllib.request.urlopen(req).read())

print(f"PID: {resp.get('prompt_id')}")
node_errs = resp.get("node_errors", {})
if node_errs:
    print(f"Node errors: {json.dumps(node_errs, indent=2)[:500]}")
else:
    print("No node errors - submitted OK")

    # Wait for completion
    pid = resp["prompt_id"]
    for i in range(120):
        time.sleep(5)
        try:
            hdata = json.loads(urllib.request.urlopen(
                f"http://127.0.0.1:8188/api/history/{pid}").read())
        except:
            continue
        if pid in hdata:
            s = hdata[pid]["status"]
            if s["completed"]:
                for nid, out in hdata[pid]["outputs"].items():
                    for img in out.get("images", []):
                        print(f"OUTPUT: {img['filename']}")
                print(f"Time: {(s['completed'] - s['started']) / 1000:.1f}s")
                break
            print(f"  [{i*5}s] {s['status_str']}")
        else:
            print(f"  [{i*5}s] waiting...")
    else:
        print("TIMEOUT")
