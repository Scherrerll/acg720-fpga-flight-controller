/* Classic script also runs when index.html is opened as a local file. */
(() => {
  const localFile = location.protocol === 'file:';
  if (localFile) document.documentElement.classList.add('local-file-entry');
  function start() {
    if (localFile) {
      document.getElementById('local-file-help').hidden = false;
      return;
    }
    // Keep module startup after DOM parsing, as the former static module did.
    const script = document.createElement('script');
    script.type = 'module';
    script.src = './app.js';
    document.head.appendChild(script);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
