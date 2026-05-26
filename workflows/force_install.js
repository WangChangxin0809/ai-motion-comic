async (page) => {
  // Try to replicate what Manager does when Install is clicked
  // The Manager likely uses a WebSocket or internal API

  // First, let's intercept network requests
  await page.evaluate(async () => {
    // Find the model list container and force-scroll it
    const allDivs = document.querySelectorAll('div');
    for (const div of allDivs) {
      // Look for divs that might be the model list
      if (div.scrollHeight > div.clientHeight && div.clientHeight > 100) {
        // Force scroll to make items render
        div.scrollTop = 0;
        await new Promise(r => setTimeout(r, 200));
        div.scrollTop = div.scrollHeight;
        await new Promise(r => setTimeout(r, 500));

        // Check for Install buttons now
        const buttons = div.querySelectorAll('button');
        const installBtns = [];
        for (const b of buttons) {
          if (b.textContent.trim() === 'Install') {
            installBtns.push(b.parentElement?.textContent?.substring(0, 60));
          }
        }
        if (installBtns.length > 0) {
          window.__installBtns = installBtns;
        }
      }
    }
    return 'done scrolling';
  });

  // Try a different approach: find if there's a React/virtual list
  return await page.evaluate(() => {
    // Check for virtual list components
    const allElements = document.querySelectorAll('[class*="virtual"], [class*="Virtual"], [class*="list"], [class*="List"], [class*="grid"], [class*="Grid"]');
    const found = [];
    for (const el of allElements) {
      if (el.children.length > 0 && el.scrollHeight > 0) {
        found.push({
          tag: el.tagName,
          className: el.className?.substring(0, 100),
          childCount: el.children.length,
          scrollH: el.scrollHeight,
          clientH: el.clientHeight
        });
      }
    }
    return JSON.stringify(found.slice(0, 15));
  });
}
