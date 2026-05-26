const fs = require('fs');
const http = require('http');

const workflowPath = 'D:/0_Study/Python_project/ai-motion-comic/workflows/SVI pro boost.json';
const comfyHost = '117.50.27.169';
const comfyPort = 8188;

const data = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

// Get all unique node types
const allTypes = new Set();
for (const node of data.nodes) {
  allTypes.add(node.type);
}

console.log('All unique node types in workflow:');
[...allTypes].sort().forEach(t => console.log('  ' + t));

// Try a minimal test - query the server for available nodes via /api/object_info
console.log('\nFetching /api/object_info to check available nodes...');
const req = http.get(`http://${comfyHost}:${comfyPort}/api/object_info`, (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => {
    try {
      const objectInfo = JSON.parse(body);
      const availableTypes = new Set(Object.keys(objectInfo));

      console.log(`Server has ${availableTypes.size} node types available`);
      console.log('\nMISSING node types (not on server):');
      let missing = [];
      for (const t of allTypes) {
        if (!availableTypes.has(t)) {
          missing.push(t);
          console.log('  MISSING: ' + t);
        }
      }
      console.log(`\nTotal missing: ${missing.length} / ${allTypes.size}`);
      console.log('\nAvailable (on server):');
      for (const t of allTypes) {
        if (availableTypes.has(t)) {
          console.log('  OK: ' + t);
        }
      }
    } catch(e) {
      console.log('Failed to parse response. Body preview:', body.slice(0, 500));
    }
  });
});

req.on('error', (e) => {
  console.error('Error:', e.message);
});
