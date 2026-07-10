(function () {
  var STORAGE_KEY = 'png-sidebar-collapsed';

  function applyState(collapsed) {
    document.body.classList.toggle('png-sidebar-collapsed', collapsed);
    var sidebar = document.querySelector('.png-sidebar');
    if (sidebar) {
      sidebar.classList.toggle('png-sidebar-collapsed', collapsed);
    }
    var toggle = document.querySelector('.png-sidebar-toggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', String(!collapsed));
      toggle.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
    }
  }

  function init() {
    var collapsed = localStorage.getItem(STORAGE_KEY) === 'true';
    applyState(collapsed);

    var toggle = document.querySelector('.png-sidebar-toggle');
    if (!toggle) {
      return;
    }
    toggle.addEventListener('click', function () {
      var next = !document.body.classList.contains('png-sidebar-collapsed');
      applyState(next);
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch (e) {
        // localStorage unavailable (e.g. private browsing) — collapse state just won't persist.
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
