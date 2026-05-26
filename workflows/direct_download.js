async (page) => {
  // The Manager uses WebSocket for model downloads
  // Try to find and use the WebSocket connection

  const result = await page.evaluate(async () => {
    // Approach: try sending a fetch to download the model via the server
    // The ComfyUI server can download files from URLs

    // First, let's see if there's a way to trigger download
    // Try the model install via a different API endpoint format

    // The Manager install queue API expects specific format
    const installPayload = {
      name: "Comfy-Org/clip_l",
      type: "clip",
      filename: "clip_l.safetensors",
      url: "https://hf-mirror.com/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors",
      hash: "",
      filesize: 246000000,
      save_path: "clip",
      base: "clip",
      description: "CLIP-L model for FLUX"
    };

    // Try POST to the queue endpoint
    try {
      const r = await fetch("/api/manager/queue/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(installPayload)
      });
      return { status: r.status, text: (await r.text()).substring(0, 200) };
    } catch(e) {
      return { error: e.message };
    }
  });

  // If that didn't work, try using the browser to download and then
  // use a different upload mechanism
  if (result.status === 500) {
    // Try starting the download via a simple fetch that the backend proxies
    const r2 = await page.evaluate(async () => {
      // Check if ComfyUI has any endpoint that downloads from URL
      const endpoints = [
        "/api/download",
        "/api/fetch",
        "/api/manager/download",
        "/api/models/download"
      ];
      const results = [];
      for (const ep of endpoints) {
        try {
          const r = await fetch(ep + "?url=https://hf-mirror.com/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors&path=models/clip/clip_l.safetensors");
          results.push(ep + ": " + r.status);
        } catch(e) {
          results.push(ep + ": err");
        }
      }
      return results;
    });
    return { firstAttempt: result, endpoints: r2 };
  }

  return result;
}
