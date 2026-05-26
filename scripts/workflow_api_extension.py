"""
ComfyUI Extension: workflow → API prompt converter
Adds POST /api/workflow_to_prompt endpoint.
"""
import json
import nodes as comfy_nodes
from aiohttp import web

_registered = False


def _is_widget_type(t):
    """Return True if this input type uses a widgets_values entry."""
    if t in ("INT", "FLOAT", "STRING", "BOOLEAN"):
        return True
    if isinstance(t, list):  # COMBO
        return True
    return False


def workflow_to_prompt(workflow: dict) -> dict:
    """Convert workflow JSON to API-compatible prompt dict."""
    links = workflow.get("links", [])
    wf_nodes = workflow.get("nodes", [])

    # Index links by id
    link_data = {}
    for link in links:
        lid, fn, fs, tn, ts, lt = link
        link_data[lid] = [str(fn), fs]

    # Resolve links per node by *name*
    node_links = {}
    for node in wf_nodes:
        lnk = {}
        for inp in node.get("inputs", []):
            li = inp.get("link")
            if li is not None and li in link_data:
                lnk[inp["name"]] = link_data[li]
        node_links[node["id"]] = lnk

    prompt = {}
    for node in wf_nodes:
        nid = str(node["id"])
        ntype = node["type"]
        if ntype not in comfy_nodes.NODE_CLASS_MAPPINGS:
            continue

        raw_wv = node.get("widgets_values", [])
        if isinstance(raw_wv, dict):
            wv_dict = raw_wv
            wv_list = []
        else:
            wv_dict = {}
            wv_list = list(raw_wv)

        cls = comfy_nodes.NODE_CLASS_MAPPINGS[ntype]
        its = cls.INPUT_TYPES()
        all_names = list(its.get("required", {}).keys()) + list(its.get("optional", {}).keys())
        all_types = {**its.get("required", {}), **its.get("optional", {})}

        inputs = {}
        linked = node_links.get(node["id"], {})

        # Walk object_info order: widget-values are aligned to this order.
        # Consume one widget value for every widget-type input (linked or not).
        # Assign widget value only when input is NOT linked.
        for name in all_names:
            t = all_types[name][0]
            if name in linked:
                inputs[name] = linked[name]
                if _is_widget_type(t):
                    if wv_list:
                        wv_list.pop(0)  # consume but discard (link overrides)
            elif _is_widget_type(t):
                if wv_dict and name in wv_dict:
                    inputs[name] = wv_dict[name]
                elif wv_list:
                    inputs[name] = wv_list.pop(0)

        prompt[nid] = {"inputs": inputs, "class_type": ntype}

    return prompt


def on_custom_loaded(app):
    global _registered
    if _registered:
        return

    @app.routes.post("/api/workflow_to_prompt")
    async def handle(request):
        body = await request.json()
        wf = body.get("workflow", {})
        if not wf:
            return web.json_response({"error": "Missing 'workflow'"}, status=400)
        try:
            prompt = workflow_to_prompt(wf)
            return web.json_response({"prompt": prompt})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    _registered = True
    print("[workflow_to_prompt] Route registered: POST /api/workflow_to_prompt")


# Fallback: try to register immediately if server is already running
try:
    from server import PromptServer

    if PromptServer.instance is not None:
        on_custom_loaded(PromptServer.instance)
except Exception:
    pass

# Minimal ComfyUI node registration (required for extension loading)
NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = None
