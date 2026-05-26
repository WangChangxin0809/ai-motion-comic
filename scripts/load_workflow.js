const fs = require('fs');
const http = require('http');

const workflowPath = process.argv[2] || 'D:/0_Study/Python_project/ai-motion-comic/workflows/SVI pro boost.json';
const comfyHost = process.argv[3] || '117.50.27.169';
const comfyPort = process.argv[4] || 8188;

const data = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

// Build link map: link_id -> {source_id, source_slot, target_id, target_slot}
const linkMap = {};
for (const link of data.links) {
  const [linkId, originId, originSlot, targetId, targetSlot, type] = link;
  linkMap[linkId] = { originId, originSlot, targetId, targetSlot, type };
}

// Build per-node output slot index map
// For each node, for each output, map the link_id to which output slot index it belongs to
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

// Convert nodes to standard format
const prompt = {};
for (const node of data.nodes) {
  const nodeEntry = {
    class_type: node.type,
    inputs: {}
  };

  if (node.inputs) {
    for (const input of node.inputs) {
      if (input.link !== null && input.link !== undefined) {
        // Connected input - find source
        const link = linkMap[input.link];
        if (link) {
          nodeEntry.inputs[input.name] = [String(link.originId), link.originSlot];
        }
      }
    }
  }

  // Handle widget values for unconnected inputs
  if (node.widgets_values && node.inputs) {
    let widgetIdx = 0;
    for (const input of node.inputs) {
      if (!(input.name in nodeEntry.inputs)) {
        // Not connected, use widget value
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
console.log(`Workflow has ${data.nodes.length} nodes, ${data.links.length} links`);
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
    console.log('Response:', body);
    try {
      const resp = JSON.parse(body);
      if (resp.prompt_id) {
        console.log(`Prompt queued! ID: ${resp.prompt_id}`);
        console.log(`View at: http://${comfyHost}:${comfyPort}/queue`);
      }
    } catch(e) {
      console.log('(raw response above)');
    }
  });
});

req.on('error', (e) => {
  console.error('Error posting workflow:', e.message);
});

req.write(payloadStr);
req.end();
