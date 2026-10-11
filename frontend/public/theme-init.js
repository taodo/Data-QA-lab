// Blocking, same-origin bootstrap: runs before the application/styles paint.
// Keep this script external so the existing script-src 'self' CSP remains intact.
(function () {
  let theme = 'dark';
  try {
    if (localStorage.getItem('dqa-theme') === 'light') theme = 'light';
  } catch { /* Preferences are optional when storage is unavailable. */ }
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#0b1424' : '#f1f5fb');
}());
