async (page) => {
  return await page.evaluate(async () => {
    // Find the scrollable model list container
    const d = document.querySelectorAll("[role=dialog]");
    const modelDialog = d[d.length - 1];

    // Try to find scrollable containers
    const scrollables = modelDialog.querySelectorAll('[style*="overflow"], [class*="scroll"], [class*="list"], [class*="grid"]');

    let found = false;
    for (const s of scrollables) {
      if (s.scrollHeight > s.clientHeight) {
        // Scroll to bottom to force render all items
        s.scrollTop = s.scrollHeight;
        await new Promise(r => setTimeout(r, 500));
        found = true;
      }
    }

    // Now look for Install buttons again
    const allButtons = modelDialog.querySelectorAll("button");
    const installBtns = [];
    for (const b of allButtons) {
      if (b.textContent.trim() === "Install") {
        const parent = b.closest('[class*="row"], [class*="item"], tr, div');
        const rowText = parent ? parent.textContent.substring(0, 80) : "no parent";
        installBtns.push(rowText);
        b.click();
        return "clicked: " + rowText;
      }
    }

    return "no install buttons found after scroll. total buttons: " + allButtons.length + ", found scrollables: " + found;
  });
}
