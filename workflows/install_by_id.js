async (page) => {
  // Try to interact with the turbogrid cells directly
  return await page.evaluate(() => {
    // Find turbogrid rows with content
    const rows = document.querySelectorAll('.tg-row');
    const rowData = Array.from(rows).map(r => ({
      text: r.textContent.trim().substring(0, 200),
      children: r.children.length,
      html: r.innerHTML.substring(0, 500)
    }));
    return JSON.stringify(rowData);
  });
}
