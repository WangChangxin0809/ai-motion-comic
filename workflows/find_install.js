async (page) => {
  // Filter Not Installed
  await page.evaluate(() => {
    const combos = document.querySelectorAll("[role=combobox], select");
    for (const cb of combos) {
      for (const o of (cb.options || [])) {
        if (o.text === "Not Installed") {
          cb.value = o.value;
          cb.dispatchEvent(new Event("change", { bubbles: true }));
          return;
        }
      }
    }
  });
  await page.waitForTimeout(1500);

  // Clear search, just look for clip_l
  await page.evaluate(() => {
    const sb = document.querySelector("input[type=search], [role=searchbox]");
    sb.value = "";
    sb.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await page.waitForTimeout(1000);

  await page.evaluate(() => {
    const sb = document.querySelector("input[type=search], [role=searchbox]");
    sb.value = "Comfy-Org/clip_l";
    sb.dispatchEvent(new Event("input", { bubbles: true }));
    sb.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await page.waitForTimeout(1500);

  // Get full dialog text
  return await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const modelDialog = d[d.length - 1];
    return modelDialog.textContent.substring(800, 2000);
  });
}
