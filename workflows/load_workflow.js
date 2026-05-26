// This script loads the novel_to_video workflow into ComfyUI
// Usage: Run in browser console or via Playwright

const fs = require('fs');
const path = require('path');

const workflowPath = path.join(__dirname, 'novel_to_video_workflow.json');
const workflowContent = fs.readFileSync(workflowPath, 'utf8');
const data = JSON.parse(workflowContent);

// Build standard ComfyUI workflow format
const graph = {
    last_node_id: data.last_node_id || 14,
    last_link_id: data.last_link_id || 29,
    nodes: Object.values(data.nodes),
    links: data.links || [],
    groups: data.groups || [],
    config: data.config || {},
    extra: {}
};

module.exports = graph;
