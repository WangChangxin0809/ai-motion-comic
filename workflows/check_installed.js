async (page) => {
  // Filter by Installed
  await page.evaluate(() => {
    const combos = document.querySelectorAll("[role=combobox], select");
    for (const cb of combos) {
      for (const o of (cb.options || [])) {
        if (o.text === "Installed") {
          cb.value = o.value;
          cb.dispatchEvent(new Event("change", { bubbles: true }));
          return;
        }
      }
    }
  });
  await page.waitForTimeout(2000);

  // Get all installed models text
  return await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const modelDialog = d[d.length - 1];
    // Get text content, parse out model names
    const text = modelDialog.textContent;
    // Find clip_l in installed list
    const hasClipL = text.includes("clip_l");
    // Get all links
    const links = Array.from(modelDialog.querySelectorAll("a")).map(a => a.textContent.substring(0, 80));
    return JSON.stringify({ hasClipL, linkCount: links.length, links: links.filter(l => l.includes("clip")) });
  });
}
