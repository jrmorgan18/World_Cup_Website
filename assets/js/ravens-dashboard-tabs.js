(function () {
  function initializeDashboardTabs() {
    var tabList = document.querySelector('.ravens-dashboard-jump[role="tablist"]');
    var tabCard = document.querySelector('[data-dashboard-tab-card]');

    if (!tabList || !tabCard) return;

    var tabs = Array.prototype.slice.call(tabList.querySelectorAll('[role="tab"]'));
    var panels = tabs.map(function (tab) {
      return document.getElementById(tab.getAttribute('aria-controls'));
    });

    if (tabs.length === 0 || panels.some(function (panel) { return !panel; })) return;

    function activateTab(tab, options) {
      var settings = options || {};
      var panelId = tab.getAttribute('aria-controls');

      tabs.forEach(function (candidate) {
        var isActive = candidate === tab;
        candidate.setAttribute('aria-selected', String(isActive));
        candidate.tabIndex = isActive ? 0 : -1;
      });

      panels.forEach(function (panel) {
        panel.hidden = panel.id !== panelId;
      });

      if (settings.updateHash && window.history && window.history.replaceState) {
        window.history.replaceState(null, '', '#' + panelId);
      }

      if (settings.focus) tab.focus();
    }

    function tabForHash() {
      var panelId = window.location.hash.slice(1);
      return tabs.find(function (tab) {
        return tab.getAttribute('aria-controls') === panelId;
      });
    }

    activateTab(tabForHash() || tabs[0]);

    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () {
        activateTab(tab, { updateHash: true });
      });

      tab.addEventListener('keydown', function (event) {
        var nextIndex;

        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
          nextIndex = (index + 1) % tabs.length;
        } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
          nextIndex = (index - 1 + tabs.length) % tabs.length;
        } else if (event.key === 'Home') {
          nextIndex = 0;
        } else if (event.key === 'End') {
          nextIndex = tabs.length - 1;
        } else {
          return;
        }

        event.preventDefault();
        activateTab(tabs[nextIndex], { focus: true, updateHash: true });
      });
    });

    window.addEventListener('hashchange', function () {
      var tab = tabForHash();
      if (tab) activateTab(tab);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboardTabs);
  } else {
    initializeDashboardTabs();
  }
}());
