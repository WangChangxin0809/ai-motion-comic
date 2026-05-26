async (page) => {
  // Try to upload via browser's native fetch to a different endpoint
  // Or try to get server to download the file itself

  // Try: have the server fetch from hf-mirror.com via ComfyUI's Python
  // Use a custom ComfyUI node or API
  const results = [];

  // Approach 1: Try different API endpoints
  const endpoints = [
    "/api/upload/model",
    "/api/models/clip/upload",
    "/api/manager/model/download"
  ];

  for (const ep of endpoints) {
    try {
      const r = await page.evaluate(async (endpoint) => {
        const resp = await fetch(endpoint, { method: "GET" });
        return endpoint + ": " + resp.status;
      }, ep);
      results.push(r);
    } catch(e) {
      results.push(ep + ": error - " + e.message);
    }
  }

  // Approach 2: Check if there's a way to run Python code
  // via the ComfyUI API
  try {
    const r = await page.evaluate(async () => {
      const resp = await fetch("/api/experiment/models/clip", { method: "OPTIONS" });
      return "OPTIONS clip: " + resp.status;
    });
    results.push(r);
  } catch(e) {
    results.push("OPTIONS failed: " + e.message);
  }

  return JSON.stringify(results);
}
