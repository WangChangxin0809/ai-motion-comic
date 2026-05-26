async (page) => {
  // First, click Refresh
  await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const modelDialog = d[d.length - 1];
    const buttons = modelDialog.querySelectorAll("button");
    for (const b of buttons) {
      if (b.textContent.trim() === "Refresh") {
        b.click();
        return "refreshed";
      }
    }
    return "no refresh";
  });
  await page.waitForTimeout(3000);

  // Search clip_l
  await page.evaluate(() => {
    const sb = document.querySelector("input[type=search], [role=searchbox]");
    sb.value = "clip_l";
    sb.dispatchEvent(new Event("input", { bubbles: true }));
    sb.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await page.waitForTimeout(2000);

  // Get ALL button texts in the model dialog
  return await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const modelDialog = d[d.length - 1];
    const all = modelDialog.textContent;
    // Check if clip_l is in results
    const hasClipL = all.includes("clip_l");
    // Find all buttons
    const buttons = modelDialog.querySelectorAll("button");
    const btnTexts = Array.from(buttons).map(b => b.textContent.trim().substring(0, 30));
    return JSON.stringify({ hasClipL, btnCount: buttons.length, btnTexts });
  });
}
