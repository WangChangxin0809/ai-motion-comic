async (page) => {
  // Change filter to Not Installed
  await page.evaluate(() => {
    const comboboxes = document.querySelectorAll("[role=combobox], select");
    for (const cb of comboboxes) {
      const opts = cb.options || [];
      for (const o of opts) {
        if (o.text === "Not Installed") {
          cb.value = o.value;
          cb.dispatchEvent(new Event("change", { bubbles: true }));
          return;
        }
      }
    }
  });
  await page.waitForTimeout(1500);

  // Search for clip_l
  await page.evaluate(() => {
    const sb = document.querySelector("input[type=search], [role=searchbox]");
    sb.value = "clip_l";
    sb.dispatchEvent(new Event("input", { bubbles: true }));
    sb.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await page.waitForTimeout(1500);

  // Try to find and click Install
  const result = await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const modelDialog = d[d.length - 1];
    if (!modelDialog) return "no dialog";

    // Try to find Install button
    const allButtons = modelDialog.querySelectorAll("button");
    for (const b of allButtons) {
      if (b.textContent.trim() === "Install" && b.offsetParent !== null) {
        b.scrollIntoView({ block: "center" });
        b.click();
        return "clicked install";
      }
    }

    return "no install button. buttons count: " + allButtons.length;
  });

  return result;
}
