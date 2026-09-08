/**
 * PWD301 — Theme Manager (Light / Dark Mode)
 * Persists theme state in localStorage and updates DOM attributes.
 */
(function () {
  'use strict';

  function getPreferredTheme() {
    const saved = localStorage.getItem('pwd301_theme');
    if (saved) return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('pwd301_theme', theme);

    const iconEl = document.getElementById('theme-icon');
    const labelEl = document.getElementById('theme-label');
    const btnEl = document.getElementById('theme-toggle-btn');

    if (iconEl) {
      if (theme === 'dark') {
        // Sun icon for switching to light mode
        iconEl.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
      } else {
        // Moon icon for switching to dark mode
        iconEl.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
      }
    }

    if (labelEl) {
      labelEl.textContent = theme === 'dark' ? 'Chế độ Sáng' : 'Chế độ Tối';
    }

    if (btnEl) {
      const title = theme === 'dark' ? 'Chuyển sang chế độ Sáng' : 'Chuyển sang chế độ Tối';
      btnEl.title = title;
      btnEl.setAttribute('aria-label', title);
    }
  }

  // Initialize theme on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function () {
    const currentTheme = getPreferredTheme();
    applyTheme(currentTheme);

    const toggleBtns = document.querySelectorAll('[data-action="toggle-theme"]');
    toggleBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const cur = document.documentElement.getAttribute('data-theme') || 'light';
        const next = cur === 'dark' ? 'light' : 'dark';
        applyTheme(next);
      });
    });
  });

  // Apply immediately to prevent flash of wrong theme
  const initialTheme = getPreferredTheme();
  document.documentElement.setAttribute('data-theme', initialTheme);
  document.documentElement.setAttribute('data-bs-theme', initialTheme);

  window.PWD = window.PWD || {};
  window.PWD.theme = {
    apply: applyTheme,
    get: getPreferredTheme,
    toggle: function () {
      const cur = document.documentElement.getAttribute('data-theme') || 'light';
      const next = cur === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    }
  };
})();
