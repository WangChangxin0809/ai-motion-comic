async (page) => {
  return await page.evaluate(() => {
    // Look for Manager's internal API in global scope
    const globals = Object.keys(window).filter(k =>
      k.toLowerCase().includes("manager") ||
      k.toLowerCase().includes("cmm") ||
      k.toLowerCase().includes("install") ||
      k.toLowerCase().includes("model")
    );

    // Also check for WebSocket connections
    const wsInfo = [];
    if (window.__comfyui_manager_ws) {
      wsInfo.push("found __comfyui_manager_ws");
    }

    // Check for common Manager global variables
    const mgrGlobals = [];
    for (const key of Object.keys(window)) {
      const val = window[key];
      if (val && typeof val === 'object' && val !== null) {
        if (typeof val.installModel === 'function' ||
            typeof val.queueInstall === 'function' ||
            typeof val.downloadModel === 'function') {
          mgrGlobals.push(key + ": has install/queue/download methods");
        }
      }
    }

    return JSON.stringify({
      globals: globals.slice(0, 20),
      wsInfo,
      mgrGlobals
    });
  });
}
