const fs = require('fs');
const path = require('path');

// Read workflow and generate a self-contained JavaScript file
const workflowPath = 'D:/0_Study/Python_project/ai-motion-comic/workflows/SVI pro boost.json';
const workflowData = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

// The Playwright run-code script that loads the workflow via ComfyUI's app API
const script = `
async (page) => {
  const workflow = ${JSON.stringify(workflowData)};

  const result = await page.evaluate((wf) => {
    try {
      // ComfyUI with rgthree/Swwan uses loadGraphData
      if (typeof app !== 'undefined' && app.graph) {
        app.graph.clear();
        app.loadGraphData(wf);
        return { success: true, method: 'app.loadGraphData', nodes: wf.nodes?.length };
      }
      return { success: false, error: 'app not available' };
    } catch(e) {
      return { success: false, error: e.message };
    }
  }, workflow);

  await page.waitForTimeout(2000);
  return result;
}
`;

const outPath = 'D:/0_Study/Python_project/ai-motion-comic/scripts/run_inject.js';
fs.writeFileSync(outPath, script);
console.log('Generated injection script:', outPath);
console.log('Size:', (script.length / 1024).toFixed(1), 'KB');
