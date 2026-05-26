const fs = require('fs');
const http = require('http');

const workflowPath = 'D:/0_Study/Python_project/ai-motion-comic/workflows/SVI pro boost.json';
const comfyHost = '117.50.27.169';
const comfyPort = 8188;

const data = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

// Build link map
const linkMap = {};
for (const link of data.links) {
  const [linkId, originId, originSlot, targetId, targetSlot, type] = link;
  linkMap[linkId] = { originId, originSlot, targetId, targetSlot, type };
}

// First pass: build SetNode/GetNode mapping by label
// SetNode: widgets_values[0] is the label, input is the value being set
// GetNode: widgets_values[0] is the label, output is the retrieved value
const setNodes = {};  // label -> { nodeId, sourceNodeId, sourceSlot }
const getNodes = {};  // label -> [nodeIds]
const rerouteNodes = {}; // nodeId -> { sourceNodeId, sourceSlot }

for (const node of data.nodes) {
  if (node.type === 'SetNode' && node.widgets_values) {
    const label = node.widgets_values[0];
    // Find what feeds into this SetNode
    if (node.inputs && node.inputs[0] && node.inputs[0].link !== null) {
      const link = linkMap[node.inputs[0].link];
      if (link) {
        setNodes[label] = { nodeId: node.id, sourceNodeId: link.originId, sourceSlot: link.originSlot };
      }
    }
  } else if (node.type === 'GetNode' && node.widgets_values) {
    const label = node.widgets_values[0];
    if (!getNodes[label]) getNodes[label] = [];
    getNodes[label].push(node.id);
  } else if (node.type === 'Reroute' && node.inputs && node.inputs[0]) {
    if (node.inputs[0].link !== null) {
      const link = linkMap[node.inputs[0].link];
      if (link) {
        rerouteNodes[node.id] = { sourceNodeId: link.originId, sourceSlot: link.originSlot };
      }
    }
  }
}

console.log('SetNode labels:', Object.keys(setNodes));
console.log('GetNode labels:', Object.keys(getNodes));

// Build a mapping: nodeId -> replacement { sourceNodeId, sourceSlot }
const replacements = {};

// For each GetNode, map to its SetNode's source
for (const [label, getNodeIds] of Object.entries(getNodes)) {
  if (setNodes[label]) {
    const { sourceNodeId, sourceSlot } = setNodes[label];
    for (const getNodeId of getNodeIds) {
      replacements[getNodeId] = { sourceNodeId, sourceSlot };
    }
  } else {
    console.log(`WARNING: GetNode '${label}' has no matching SetNode`);
  }
}

// Build output slot index map for each node
const nodeOutputSlotMap = {};
for (const node of data.nodes) {
  const slotMap = {};
  if (node.outputs) {
    node.outputs.forEach((output, idx) => {
      if (output.links) {
        for (const linkId of output.links) {
          slotMap[linkId] = idx;
        }
      }
    });
  }
  nodeOutputSlotMap[node.id] = slotMap;
}

// Build a reverse link map: target_node_id -> { sourceNodeId, sourceSlot, inputName }
const reverseLinks = {};
for (const link of data.links) {
  const [linkId, originId, originSlot, targetId, targetSlot, type] = link;
  // Find the input name on the target node
  const targetNode = data.nodes.find(n => n.id === targetId);
  if (targetNode && targetNode.inputs) {
    const input = targetNode.inputs[targetSlot];
    if (input) {
      reverseLinks[targetId] = reverseLinks[targetId] || [];
      reverseLinks[targetId].push({
        inputName: input.name,
        originId,
        originSlot,
        inputIndex: targetSlot,
        linkId
      });
    }
  }
}

// Now build the prompt, skipping SetNode/GetNode/Reroute and rewriting connections
const nodesToSkip = new Set();
for (const n of data.nodes) {
  if (n.type === 'SetNode' || n.type === 'GetNode' || n.type === 'Reroute') {
    nodesToSkip.add(n.id);
  }
}

// For nodes that have inputs connected to a GetNode/Reroute, resolve the real source
function resolveSource(nodeId, inputSlot) {
  const node = data.nodes.find(n => n.id === nodeId);
  if (!node) return null;

  // Check if this input is connected
  const input = node.inputs?.[inputSlot];
  if (!input || input.link === null) return null;

  const link = linkMap[input.link];
  if (!link) return null;

  // Check if source is a GetNode or Reroute
  if (replacements[link.originId]) {
    // Replace with the SetNode's source
    return replacements[link.originId];
  }
  if (rerouteNodes[link.originId]) {
    // Follow the reroute, recursively resolve
    const reroute = rerouteNodes[link.originId];
    return resolveSource(reroute.sourceNodeId, reroute.sourceSlot) || reroute;
  }

  return { sourceNodeId: link.originId, sourceSlot: link.originSlot };
}

const prompt = {};
let skippedNodes = 0;

for (const node of data.nodes) {
  if (nodesToSkip.has(node.id)) {
    skippedNodes++;
    continue;
  }

  const nodeEntry = {
    class_type: node.type,
    inputs: {}
  };

  if (node.inputs) {
    for (let i = 0; i < node.inputs.length; i++) {
      const input = node.inputs[i];
      if (input.link !== null && input.link !== undefined) {
        const resolved = resolveSource(node.id, i);
        if (resolved) {
          // Check if resolved source is also a node to skip
          if (nodesToSkip.has(resolved.sourceNodeId)) {
            // Skip this connection - the SetNode is the source, not the SetNode itself
            // The resolved source should already be the real source
          }
          nodeEntry.inputs[input.name] = [String(resolved.sourceNodeId), resolved.sourceSlot];
        }
        // If couldn't resolve (dead link), leave input unset
      }
    }
  }

  // Handle widget values for unconnected inputs
  if (node.widgets_values && node.inputs) {
    let widgetIdx = 0;
    for (const input of node.inputs) {
      if (!(input.name in nodeEntry.inputs)) {
        const val = node.widgets_values[widgetIdx];
        if (val !== undefined) {
          nodeEntry.inputs[input.name] = val;
        }
        widgetIdx++;
      }
    }
  }

  prompt[String(node.id)] = nodeEntry;
}

console.log(`Original nodes: ${data.nodes.length}, Skipped (SetNode/GetNode/Reroute): ${skippedNodes}`);
console.log(`Final prompt nodes: ${Object.keys(prompt).length}`);

// Build the API payload
const payload = {
  client_id: 'playwright-cli-loader',
  prompt: prompt,
  extra_data: {
    extra_pnginfo: {
      workflow: data
    }
  }
};

const payloadStr = JSON.stringify(payload);
console.log(`Payload size: ${(payloadStr.length / 1024).toFixed(1)} KB`);
console.log(`Posting to http://${comfyHost}:${comfyPort}/api/prompt ...`);

// POST to ComfyUI
const req = http.request({
  hostname: comfyHost,
  port: comfyPort,
  path: '/api/prompt',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(payloadStr)
  }
}, (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => {
    console.log(`Status: ${res.statusCode}`);
    try {
      const resp = JSON.parse(body);
      if (resp.prompt_id) {
        console.log(`Prompt queued! ID: ${resp.prompt_id}`);
        console.log(`View at: http://${comfyHost}:${comfyPort}/queue`);
      } else {
        console.log('Response:', JSON.stringify(resp, null, 2).slice(0, 2000));
      }
    } catch(e) {
      console.log('Response:', body.slice(0, 2000));
    }
  });
});

req.on('error', (e) => {
  console.error('Error posting workflow:', e.message);
});

req.write(payloadStr);
req.end();
