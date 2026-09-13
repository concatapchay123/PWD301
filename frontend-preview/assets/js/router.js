/**
 * PWD301 — Online Course Management Platform
 * Hash-based View Router & Perspective Navigation
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};

  class Router {
    constructor() {
      this.routes = {};
      this.currentRoute = null;
      this.outlet = null;

      window.addEventListener('hashchange', () => this.handleRouting());
    }

    init(outletId = 'router-outlet') {
      this.outlet = document.getElementById(outletId);
      if (!window.location.hash) {
        // Default route based on active store perspective
        const p = window.PWD.store.getPerspective();
        if (p === 'public') window.location.hash = '#/public/catalog';
        else if (p === 'student') window.location.hash = '#/student/dashboard';
        else if (p === 'instructor') window.location.hash = '#/instructor/dashboard';
        else if (p === 'admin') window.location.hash = '#/admin/dashboard';
      } else {
        this.handleRouting();
      }
    }

    register(pattern, handler, requiredPerspective = null) {
      this.routes[pattern] = {
        handler,
        requiredPerspective
      };
    }

    navigate(hash) {
      window.location.hash = hash;
    }

    matchRoute(hash) {
      const cleanHash = hash.replace(/^#/, '').split('?')[0] || '/';
      
      for (const pattern in this.routes) {
        // Simple parameter matcher (e.g. /student/course/:id)
        const regexPattern = '^' + pattern.replace(/:[a-zA-Z0-9_]+/g, '([^/]+)') + '$';
        const match = cleanHash.match(new RegExp(regexPattern));
        
        if (match) {
          const paramNames = (pattern.match(/:[a-zA-Z0-9_]+/g) || []).map(p => p.substring(1));
          const params = {};
          paramNames.forEach((name, idx) => {
            params[name] = match[idx + 1];
          });
          return {
            pattern,
            params,
            routeInfo: this.routes[pattern]
          };
        }
      }
      return null;
    }

    handleRouting() {
      const hash = window.location.hash;
      const matched = this.matchRoute(hash);

      if (!matched) {
        console.warn('No route matched for:', hash);
        if (this.outlet) {
          this.outlet.innerHTML = window.PWD.components.emptyState(
            'Không tìm thấy trang',
            'Đường dẫn bạn yêu cầu không tồn tại trong hệ thống demo.',
            `<a href="#/student/dashboard" class="btn btn-primary btn-sm">Về Tổng quan</a>`,
            'alertCircle'
          );
        }
        return;
      }

      const { pattern, params, routeInfo } = matched;
      this.currentRoute = { pattern, params };

      // Update active sidebar link
      this.syncSidebarActive(hash);

      // Render view
      if (this.outlet) {
        try {
          const html = routeInfo.handler(params);
          this.outlet.innerHTML = html;
          
          // Scroll workspace to top
          window.scrollTo(0, 0);
          const workspace = document.querySelector('.app-main-workspace');
          if (workspace) workspace.scrollTop = 0;

          // Call post-render hooks if defined
          if (window.PWD.activeViewInit && typeof window.PWD.activeViewInit === 'function') {
            window.PWD.activeViewInit(params);
          }

          // Trigger GSAP motion entrance and interactions for newly rendered view
          if (window.PWD.motion) {
            window.PWD.motion.animatePageEntrance();
            window.PWD.motion.initScrollTriggers();
            window.PWD.motion.bindMicroInteractions(this.outlet);
          }
        } catch (err) {
          console.error('Error rendering view for route:', hash, err);
          this.outlet.innerHTML = window.PWD.components.emptyState(
            'Đã xảy ra lỗi hiển thị',
            'Chi tiết: ' + err.message,
            `<button onclick="location.reload()" class="btn btn-secondary btn-sm">Tải lại trang</button>`,
            'alertTriangle'
          );
        }
      }
    }

    syncSidebarActive(currentHash) {
      const links = document.querySelectorAll('.sidebar-link');
      links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentHash.startsWith(href)) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });
    }
  }

  window.PWD.router = new Router();
})();
