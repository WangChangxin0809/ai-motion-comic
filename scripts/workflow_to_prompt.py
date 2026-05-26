"""
ComfyUI Extension: /api/workflow_to_prompt
Converts workflow JSON → API prompt format.
Install: copy to ComfyUI/custom_nodes/workflow_to_prompt.py
"""
import json
import folder_paths
from aiohttp import web


def workflow_to_prompt(workflow: dict) -> dict:
    """Convert a workflow JSON to API-compatible prompt format."""

    # Get all registered node types for correct input ordering
    from nodes import NODE_CLASS_MAPPINGS

    links = workflow.get("links", [])
    nodes = workflow.get("nodes", [])

    # Build link map: (to_node_id, to_slot) -> [from_node_id_str, from_slot]
    link_map = {}
    for link in links:
        lid, from_node, from_slot, to_node, to_slot, ltype = link
        link_map[(to_node, to_slot)] = [str(from_node), from_slot]

    prompt = {}
    for node in nodes:
        nid = str(node["id"])
        ntype = node["type"]
        wv = list(node.get("widgets_values", []))

        if ntype not in NODE_CLASS_MAPPINGS:
            continue

        cls = NODE_CLASS_MAPPINGS[ntype]
        input_types = cls.INPUT_TYPES()
        required = input_types.get("required", {})
        optional = input_types.get("optional", {})

        inputs = {}
        for inp_name in list(required.keys()) + list(optional.keys()):
            # Check if this input is connected via a link
            slot_idx = len(inputs)  # current slot index
            key = (node["id"], slot_idx)
            if key in link_map:
                inputs[inp_name] = link_map[key]
            elif wv:
                inputs[inp_name] = wv.pop(0)

        prompt[nid] = {"inputs": inputs, "class_type": ntype}

    return prompt


# Register API route
def setup():
    """Called by ComfyUI to register routes."""
    try:
        from server import PromptServer
        server = PromptServer.instance

        @server.routes.post("/api/workflow_to_prompt")
        async def handle(request):
            body = await request.json()
            wf = body.get("workflow", {})
            if not wf:
                return web.json_response({"error": "Missing 'workflow' in body"}, status=400)
            prompt = workflow_to_prompt(wf)
            return web.json_response({"prompt": prompt})

        print("[workflow_to_prompt] Registered /api/workflow_to_prompt")
    except Exception as e:
        print(f"[workflow_to_prompt] Failed to register: {e}")


# Also register for ComfyUI's node system
NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = None
