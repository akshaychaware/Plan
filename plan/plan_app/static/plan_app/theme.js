(() => {
  let theme = null;
  try {
    theme = localStorage.getItem('theme');
  } catch {}
  document.documentElement.dataset.theme =
    theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
})();
