async (page) => {
  const result = await page.evaluate(() => {
    // Find the search input in the Model Manager dialog
    const dialogs = document.querySelectorAll('.p-dialog');
    for (const d of dialogs) {
      if (d.textContent.includes('external models') || d.textContent.includes('Save Path')) {
        const inp = d.querySelector('input');
        if (inp) {
          inp.value = 'wan 2.2 image';
          inp.dispatchEvent(new Event('input', {bubbles: true}));
          inp.dispatchEvent(new Event('change', {bubbles: true}));
          return 'searched for: wan 2.2 image';
        }
        return 'no input found in model dialog';
      }
    }
    return 'no model dialog found. Dialogs found: ' + dialogs.length;
  });
  await page.waitForTimeout(2000);
  return result;
};
