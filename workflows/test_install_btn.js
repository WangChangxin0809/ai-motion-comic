async (page) => {
  // Search for SDXL-Turbo (should have Install button since not installed)
  await page.evaluate(() => {
    const sb = document.querySelector("input[type=search], [role=searchbox]");
    sb.value = "SDXL-Turbo";
    sb.dispatchEvent(new Event("input", { bubbles: true }));
    sb.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await page.waitForTimeout(2000);

  return await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const md = d[d.length - 1];
    const text = md.textContent;
    // Find "Install" in the text
    const idx = text.indexOf("Install");
    return idx >= 0 ? text.substring(idx, idx + 300) : "no install text found in: " + text.substring(800, 2000);
  });
}
