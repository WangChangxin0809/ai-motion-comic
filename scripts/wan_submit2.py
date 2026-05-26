"""Build and submit Wan I2V API prompt, using object_info for correct input mapping."""
import json, urllib.request, time

WF_PATH = "/root/ComfyUI/user/default/workflows/wan22_i2v_kijai.json"
IMAGE = "AnimeShrine_00001_.png"
PROMPT = "the shrine maiden slowly turns her head toward the camera and smiles gently, cherry blossom petals drifting across the scene, her black ponytail swaying softly in the breeze, warm sunset light flickering through the torii gate, cinematic slow motion"

# Load workflow
with open(WF_PATH) as f:
    wf = json.load(f)

# Get object_info for correct input ordering
obj_info = json.loads(urllib.request.urlopen(
    "http://127.0.0.1:8188/api/object_info").read())

# Build link map: (to_node_id, to_slot) -> [from_node_str, from_slot]
link_map = {}
for link in wf["links"]:
    lid, fn, fs, tn, ts, ltype = link
    link_map[(tn, ts)] = [str(fn), fs]

# Build node reverse lookup: which links go to which input names
node_link_inputs = {}  # node_id -> {input_name: [from_node, from_slot]}
for (tn, ts), link_val in link_map.items():
    if tn not in node_link_inputs:
        node_link_inputs[tn] = {}
    # Get input name from workflow nodes
    for node in wf["nodes"]:
        if node["id"] == tn:
            wf_inputs = node.get("inputs", [])
            if ts < len(wf_inputs):
                node_link_inputs[tn][wf_inputs[ts]["name"]] = link_val
            break

# Build API prompt
api = {}
for node in wf["nodes"]:
    nid = node["id"]
    ntype = node["type"]
    wv = list(node.get("widgets_values", []))
    node_inputs = {}

    if ntype not in obj_info:
        continue

    info = obj_info[ntype]
    required = info["input"].get("required", {})
    optional = info["input"].get("optional", {})

    # Iterate all inputs in order: required first, then optional
    links_for_node = node_link_inputs.get(nid, {})

    for inp_name, inp_type in list(required.items()) + list(optional.items()):
        if inp_name in links_for_node:
            node_inputs[inp_name] = links_for_node[inp_name]
        elif wv:
            node_inputs[inp_name] = wv.pop(0)

    api[str(nid)] = {"inputs": node_inputs, "class_type": ntype}

# Override image and prompt
for nid, nd in api.items():
    if nd["class_type"] == "LoadImage":
        nd["inputs"]["image"] = IMAGE
        print(f"Set image: {IMAGE}")
    if nd["class_type"] == "WanVideoTextEncode":
        nd["inputs"]["prompt"] = PROMPT
        print(f"Set prompt: {PROMPT[:80]}...")

# Submit
body = json.dumps({"prompt": api}).encode()
req = urllib.request.Request("http://127.0.0.1:8188/api/prompt", data=body)
resp = json.loads(urllib.request.urlopen(req).read())

pid = resp.get("prompt_id", "NONE")
nerrs = resp.get("node_errors", {})
if nerrs:
    print(f"Node errors ({len(nerrs)}):")
    for k, v in list(nerrs.items())[:10]:
        print(f"  Node {k}: {str(v)[:120]}")
else:
    print(f"Submitted OK, PID: {pid}")

# Wait if submitted
if pid and pid != "NONE" and not nerrs:
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
                    for gif in out.get("gifs", []):
                        print(f"GIF: {gif['filename']}")
                break
            print(f"  [{i*5}s] {s['status_str']}")
        else:
            print(f"  [{i*5}s] waiting...")
    else:
        print("TIMEOUT - check manually")
