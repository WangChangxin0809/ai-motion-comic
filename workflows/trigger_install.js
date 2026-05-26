async (page) => {
  // Try different Manager install API endpoints
  const tests = [
    { url: "/api/manager/queue/install", body: { name: "Comfy-Org/clip_l", type: "clip" } },
  ];

  const results = [];
  for (const test of tests) {
    try {
      const r = await page.evaluate(async (t) => {
        const resp = await fetch(t.url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(t.body)
        });
        return t.url + ": " + resp.status + " - " + (await resp.text()).substring(0, 200);
      }, test);
      results.push(r);
    } catch(e) {
      results.push(test.url + ": error - " + e.message);
    }
  }

  // Also try the install from the model entry directly
  await page.evaluate(() => {
    const sb = document.querySelector("input[type=search], [role=searchbox]");
    sb.value = "Comfy-Org/clip_l";
    sb.dispatchEvent(new Event("input", { bubbles: true }));
    sb.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await page.waitForTimeout(2000);

  // Check what links/buttons exist now
  const final = await page.evaluate(() => {
    const d = document.querySelectorAll("[role=dialog]");
    const md = d[d.length - 1];
    const links = Array.from(md.querySelectorAll("a")).map(a => ({
      text: a.textContent.substring(0, 60),
      href: a.href?.substring(0, 100)
    }));
    const buttons = Array.from(md.querySelectorAll("button")).map(b => ({
      text: b.textContent.trim(),
      visible: !!b.offsetParent
    }));
    return JSON.stringify({ links, buttons });
  });

  return JSON.stringify({ results, final: JSON.parse(final) });
}
