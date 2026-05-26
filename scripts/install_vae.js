const result = await page.evaluate(() => {
  const d = document.querySelectorAll('.p-dialog')[1];
  const btns = [...d.querySelectorAll('button')];
  const installBtns = btns.filter(b => b.textContent.trim() === 'Install');
  for (const b of installBtns) {
    const row = b.closest('[class*="row"]');
    if (row && row.textContent.includes('FLUX')) {
      b.click();
      return 'clicked FLUX VAE install';
    }
  }
  const stops = btns.filter(b => b.textContent.includes('Stop')).length;
  return 'not found. installs=' + installBtns.length + ' stops=' + stops;
});
await page.waitForTimeout(1000);
return result;
