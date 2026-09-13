/**
 * PWD301 — Master GSAP Motion & Interaction Engine
 * Implements full GSAP skills suite:
 * - gsap-core (transforms, autoAlpha, tweens, easings)
 * - gsap-timeline (sequenced choreography, labels, position params)
 * - gsap-scrolltrigger (scroll reveals, scaleX progress bars, lifecycle cleanup)
 * - gsap-performance (compositor-only transforms, gsap.quickTo, avoiding layout thrashing)
 * - gsap-utils (clamp, mapRange, interpolate, random, toArray)
 *
 * Provides luxury, 60fps hardware-accelerated animations, micro-interactions, responsive orchestration,
 * and strict prefers-reduced-motion accessibility.
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};

  const ENTRANCE_STORAGE_KEY = 'pwd301_initial_entrance_done';

  const PWDMotion = {
    initialized: false,
    _entranceCompleted: false,
    mm: null,

    /**
     * Check if initial web entrance animation has already played in this browser session.
     * Strict UX invariant: entrance animation appears strictly ONCE on first landing;
     * all subsequent navigations, back-and-forth operations, and component transitions are clean and instant.
     */
    hasEntered() {
      if (this._entranceCompleted) return true;
      try {
        if (sessionStorage.getItem(ENTRANCE_STORAGE_KEY) === 'true') {
          this._entranceCompleted = true;
          return true;
        }
      } catch (e) {
        // Fallback to in-memory flag if sessionStorage is restricted
      }
      return false;
    },

    /**
     * Mark the initial web entrance as completed for this session.
     */
    markEntered() {
      this._entranceCompleted = true;
      try {
        sessionStorage.setItem(ENTRANCE_STORAGE_KEY, 'true');
      } catch (e) {}
    },

    /**
     * Reset session entrance state (for testing or re-entrance flows).
     */
    resetEntrance() {
      this._entranceCompleted = false;
      try {
        sessionStorage.removeItem(ENTRANCE_STORAGE_KEY);
      } catch (e) {}
    },

    init() {
      if (typeof window.gsap === 'undefined') {
        console.warn('[PWDMotion] GSAP library not loaded, skipping motion initialization.');
        return;
      }

      // Guard: prevent double-initialization in the same document lifecycle
      if (this.initialized) {
        return;
      }
      this.initialized = true;

      // 1. Register GSAP Plugins
      if (typeof window.ScrollTrigger !== 'undefined') {
        window.gsap.registerPlugin(window.ScrollTrigger);
      }

      // 2. Set Project-Wide GSAP Defaults
      window.gsap.defaults({
        duration: 0.45,
        ease: 'power2.out',
      });

      // 3. Setup Responsive & Reduced Motion via gsap.matchMedia()
      this.setupMatchMedia();

      // 4. Initial Page Entrance Animation (strictly once per session)
      this.animatePageEntrance();

      // 5. Initialize ScrollTriggers for elements in view
      this.initScrollTriggers();

      // 6. Bind Micro-Interactions (Hover, 3D Tilt, Click, Press)
      this.bindMicroInteractions();

      // 7. Ambient Floating Animation for AI Launcher Mascot
      this.initOctopusMascotMotion();

      // 8. Bind Mobile Offcanvas Drawer Animations
      this.initMobileDrawerMotion();
    },

    /**
     * gsap.matchMedia() setup for responsive adaptations and prefers-reduced-motion
     */
    setupMatchMedia() {
      if (typeof window.gsap.matchMedia !== 'function') return;

      this.mm = window.gsap.matchMedia();

      this.mm.add(
        {
          isDesktop: '(min-width: 992px)',
          isTablet: '(min-width: 768px) and (max-width: 991px)',
          isMobile: '(max-width: 767px)',
          reduceMotion: '(prefers-reduced-motion: reduce)',
        },
        (context) => {
          const { reduceMotion, isMobile } = context.conditions;

          if (reduceMotion) {
            // vestibular disorder compliance: zero-out animation durations
            window.gsap.globalTimeline.timeScale(100);
            return;
          } else {
            window.gsap.globalTimeline.timeScale(1);
          }

          if (isMobile) {
            // Mobile adjustments: clear transform props to prevent touch layout clipping
            window.gsap.set('.app-main-workspace', { clearProps: 'transform' });
          }
        }
      );
    },

    /**
     * Coordinated Page Load / View Transition Timeline (gsap-timeline)
     * STRICT CONTRACT: Only runs ONCE on the very first time entering the website in a session.
     * All subsequent navigations, back-and-forth operations, and component transitions are 100% clean
     * with zero flickering and zero popping/rising effects.
     */
    animatePageEntrance() {
      if (typeof window.gsap === 'undefined') return;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      // Selectors for elements involved in entrance layout
      const entranceTargets = [
        '.app-topbar',
        '.app-sidebar .sidebar-item',
        '.page-header',
        '.page-header-content',
        '.hero-welcome-card',
        '.metric-card',
        '.stat-card',
        '.app-main-workspace .card:not(.metric-card):not(.stat-card)'
      ].join(', ');

      if (this.hasEntered() || prefersReduced) {
        // Subsequent navigations or reduced motion:
        // Immediate return ensures clean, native, zero-flicker rendering
        return;
      }

      // First time entering the web: Mark entrance as done immediately so no other concurrent event or route triggers it
      this.markEntered();

      const tl = window.gsap.timeline({
        defaults: { ease: 'power3.out', duration: 0.45 },
        onComplete: () => {
          // Clean up inline transform/opacity properties after entrance animation completes
          // so native CSS rendering, layout, and hover states remain clean and unencumbered
          window.gsap.set(entranceTargets, {
            clearProps: 'transform,opacity,visibility'
          });
        }
      });

      // Topbar slide down
      const topbar = document.querySelector('.app-topbar');
      if (topbar) {
        tl.fromTo(
          topbar,
          { y: -24, autoAlpha: 0 },
          { y: 0, autoAlpha: 1, duration: 0.4 },
          0
        );
      }

      // Sidebar links stagger reveal
      const sidebarLinks = window.gsap.utils.toArray('.app-sidebar .sidebar-item');
      if (sidebarLinks.length > 0) {
        tl.fromTo(
          sidebarLinks,
          { x: -16, autoAlpha: 0 },
          { x: 0, autoAlpha: 1, stagger: 0.025, duration: 0.35, ease: 'power2.out' },
          0.08
        );
      }

      // Page header / Breadcrumbs
      const pageHeader = document.querySelector('.page-header, .page-header-content');
      if (pageHeader) {
        tl.fromTo(
          pageHeader,
          { y: 16, autoAlpha: 0 },
          { y: 0, autoAlpha: 1, duration: 0.38 },
          0.12
        );
      }

      // Hero welcome banner spring entrance
      const heroCard = document.querySelector('.hero-welcome-card');
      if (heroCard) {
        heroCard.dataset.gsapRevealed = 'true';
        tl.fromTo(
          heroCard,
          { y: 20, autoAlpha: 0, scale: 0.985 },
          { y: 0, autoAlpha: 1, scale: 1, duration: 0.5, ease: 'back.out(1.2)' },
          0.16
        );
      }

      // KPI Metric Cards stagger in
      const metricCards = window.gsap.utils.toArray('.metric-card, .stat-card');
      if (metricCards.length > 0) {
        metricCards.forEach((c) => (c.dataset.gsapRevealed = 'true'));
        tl.fromTo(
          metricCards,
          { y: 22, autoAlpha: 0, scale: 0.97 },
          { y: 0, autoAlpha: 1, scale: 1, stagger: 0.05, duration: 0.42, ease: 'power2.out' },
          0.2
        );
      }

      // Primary cards in visible workspace
      const mainCards = window.gsap.utils.toArray('.app-main-workspace .card:not(.metric-card):not(.stat-card)');
      if (mainCards.length > 0) {
        mainCards.forEach((c) => (c.dataset.gsapRevealed = 'true'));
        tl.fromTo(
          mainCards,
          { y: 20, autoAlpha: 0 },
          { y: 0, autoAlpha: 1, stagger: 0.07, duration: 0.42, ease: 'power2.out' },
          0.26
        );
      }
    },

    /**
     * Clean up orphaned ScrollTriggers across view changes (gsap-scrolltrigger lifecycle)
     */
    cleanupScrollTriggers() {
      if (typeof window.ScrollTrigger !== 'undefined') {
        window.ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
      }
    },

    /**
     * ScrollTrigger Batching for Below-the-Fold Scroll-Driven Reveals
     */
    initScrollTriggers() {
      if (typeof window.ScrollTrigger === 'undefined' || typeof window.gsap === 'undefined') return;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced || this.hasEntered()) return;

      // Clean up any existing triggers before registering new view triggers
      this.cleanupScrollTriggers();

      // Batch reveals for dynamic cards and table rows that were not revealed by page entrance
      const scrollTargets = window.gsap.utils.toArray('.syllabus-row, .course-card, .app-table tbody tr');
      if (scrollTargets.length > 0) {
        window.ScrollTrigger.batch(scrollTargets, {
          interval: 0.08,
          batchMax: 4,
          onEnter: (batch) => {
            window.gsap.fromTo(
              batch,
              { autoAlpha: 0, y: 16 },
              { autoAlpha: 1, y: 0, stagger: 0.05, duration: 0.4, ease: 'power2.out', overwrite: 'auto' }
            );
          },
          start: 'top 90%',
          once: true,
        });
      }

      // Animated Progress Bars on Scroll using transform scaleX (gsap-performance compositor rule)
      const progressBars = window.gsap.utils.toArray('.progress-bar-fill, .progress-bar');
      progressBars.forEach((bar) => {
        const targetWidth = bar.style?.width || bar.getAttribute?.('style')?.match(/width:\s*([^;]+)/)?.[1];
        if (targetWidth && targetWidth !== '0%') {
          if (bar.style) bar.style.transformOrigin = 'left center';
          window.ScrollTrigger.create({
            trigger: bar,
            start: 'top 95%',
            once: true,
            onEnter: () => {
              window.gsap.fromTo(
                bar,
                { scaleX: 0 },
                { scaleX: 1, duration: 0.75, ease: 'power2.out' }
              );
            },
          });
        }
      });
    },

    /**
     * Interactive Hover, Magnetic Press & 3D Tilt Micro-Interactions
     * Uses gsap-core, gsap-performance (gsap.quickTo), and gsap-utils (clamp, mapRange)
     * Provides rich floating elevation, 3D tilt, elastic button press, and table row hover
     */
    bindMicroInteractions(root = document) {
      if (typeof window.gsap === 'undefined') return;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) return;

      const isDesktop = window.matchMedia('(min-width: 992px)').matches;

      // 1. Card Smooth Elevation Hover & Interactive 3D Tilt (Desktop)
      const cards = window.gsap.utils.toArray(root.querySelectorAll('.card, .metric-card, .hero-welcome-card, .stat-card, .course-card'));
      cards.forEach((card) => {
        if (!card || card._hasMotionHover) return;
        card._hasMotionHover = true;

        // Hardware-acceleration hint
        if (card.style) card.style.willChange = 'transform';

        // Use gsap.quickTo for high-performance 60fps tracking
        const yTo = window.gsap.quickTo(card, 'y', { duration: 0.28, ease: 'power2.out' });

        if (isDesktop && !card.classList.contains('hero-welcome-card')) {
          const rotXTo = window.gsap.quickTo(card, 'rotationX', { duration: 0.25, ease: 'power1.out' });
          const rotYTo = window.gsap.quickTo(card, 'rotationY', { duration: 0.25, ease: 'power1.out' });

          card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const relX = e.clientX - rect.left;
            const relY = e.clientY - rect.top;

            // Map mouse coordinates to rotation (-3 to +3 deg) with gsap.utils
            const targetRotX = window.gsap.utils.mapRange(0, rect.height, 3, -3, relY);
            const targetRotY = window.gsap.utils.mapRange(0, rect.width, -3, 3, relX);

            rotXTo(window.gsap.utils.clamp(-4, 4, targetRotX));
            rotYTo(window.gsap.utils.clamp(-4, 4, targetRotY));
          });
        }

        card.addEventListener('mouseenter', () => {
          yTo(-5);
        });

        card.addEventListener('mouseleave', () => {
          yTo(0);
          if (isDesktop && !card.classList.contains('hero-welcome-card')) {
            window.gsap.to(card, {
              rotationX: 0,
              rotationY: 0,
              duration: 0.35,
              ease: 'power2.out',
              overwrite: 'auto',
            });
          }
        });
      });

      // 2. Buttons Elastic Press Interaction (gsap-core & gsap-performance)
      const buttons = window.gsap.utils.toArray(root.querySelectorAll('.btn:not(.btn-link), .topbar-icon-btn, .ai-chip-btn'));
      buttons.forEach((btn) => {
        if (!btn || btn._hasMotionPress) return;
        btn._hasMotionPress = true;

        if (btn.style) btn.style.willChange = 'transform';

        btn.addEventListener('mousedown', () => {
          window.gsap.to(btn, {
            scale: 0.95,
            duration: 0.12,
            ease: 'power1.out',
            overwrite: 'auto',
          });
        });

        const release = () => {
          window.gsap.to(btn, {
            scale: 1,
            duration: 0.28,
            ease: 'back.out(2)',
            overwrite: 'auto',
          });
        };

        btn.addEventListener('mouseup', release);
        btn.addEventListener('mouseleave', release);

        // Mobile touch feedback
        btn.addEventListener('touchstart', () => {
          window.gsap.to(btn, { scale: 0.96, duration: 0.1, overwrite: 'auto' });
        }, { passive: true });
        btn.addEventListener('touchend', release, { passive: true });
      });

      // 3. Table Rows Luminous Hover
      const tableRows = window.gsap.utils.toArray(root.querySelectorAll('.app-table tbody tr, .table tbody tr'));
      tableRows.forEach((row) => {
        if (row._hasMotionRow) return;
        row._hasMotionRow = true;

        row.addEventListener('mouseenter', () => {
          window.gsap.to(row, {
            x: 5,
            duration: 0.2,
            ease: 'power2.out',
            overwrite: 'auto',
          });
        });

        row.addEventListener('mouseleave', () => {
          window.gsap.to(row, {
            x: 0,
            duration: 0.24,
            ease: 'power2.out',
            overwrite: 'auto',
          });
        });
      });
    },

    /**
     * Ambient Floating Mascot Motion for Octopus AI Assistant (gsap-core & gsap-utils)
     */
    initOctopusMascotMotion() {
      const launcher = document.getElementById('ai-fab-launcher');
      if (!launcher || launcher._hasMascotMotion) return;
      launcher._hasMascotMotion = true;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) return;

      if (launcher.style) launcher.style.willChange = 'transform';

      // 1. Organic Idle Float using sine easing and slight random variation
      const floatDistance = window.gsap.utils.random(-8, -6);
      window.gsap.to(launcher, {
        y: floatDistance,
        duration: 2.2,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
      });

      // 2. Interactive Mascot Hover (Spring expansion)
      launcher.addEventListener('mouseenter', () => {
        window.gsap.to(launcher, {
          scale: 1.08,
          duration: 0.3,
          ease: 'back.out(2)',
          overwrite: 'auto',
        });
      });

      launcher.addEventListener('mouseleave', () => {
        window.gsap.to(launcher, {
          scale: 1,
          duration: 0.3,
          ease: 'power2.out',
          overwrite: 'auto',
        });
      });

      // 3. Avatar Mascot playful rotation
      const img = typeof launcher.querySelector === 'function' ? launcher.querySelector('.ai-fab-avatar-img') : null;
      if (img) {
        launcher.addEventListener('mouseenter', () => {
          window.gsap.to(img, {
            rotation: 8,
            duration: 0.35,
            ease: 'back.out(2)',
            overwrite: 'auto',
          });
        });

        launcher.addEventListener('mouseleave', () => {
          window.gsap.to(img, {
            rotation: 0,
            duration: 0.35,
            ease: 'power2.out',
            overwrite: 'auto',
          });
        });
      }
    },

    /**
     * Mobile Offcanvas Drawer Navigation Motion (gsap-timeline & stagger)
     */
    initMobileDrawerMotion() {
      const mobileDrawer = document.getElementById('mobile-offcanvas');
      if (!mobileDrawer || mobileDrawer._hasDrawerMotion) return;
      mobileDrawer._hasDrawerMotion = true;

      mobileDrawer.addEventListener('shown.bs.offcanvas', () => {
        const links = typeof mobileDrawer.querySelectorAll === 'function'
          ? window.gsap.utils.toArray(mobileDrawer.querySelectorAll('.sidebar-item, a'))
          : [];
        if (links.length > 0) {
          window.gsap.fromTo(
            links,
            { x: -20, autoAlpha: 0 },
            { x: 0, autoAlpha: 1, stagger: 0.03, duration: 0.32, ease: 'power2.out' }
          );
        }
      });
    },

    /**
     * Fluid Expand for AI Chat Window (Spring Back.out)
     */
    openAIChat(windowEl) {
      if (!windowEl) return;
      windowEl.classList.remove('d-none');

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) return;

      window.gsap.fromTo(
        windowEl,
        {
          autoAlpha: 0,
          scale: 0.84,
          y: 20,
          transformOrigin: 'bottom right',
        },
        {
          autoAlpha: 1,
          scale: 1,
          y: 0,
          duration: 0.38,
          ease: 'back.out(1.4)',
          overwrite: 'auto',
        }
      );
    },

    /**
     * Fluid Dismiss for AI Chat Window
     */
    closeAIChat(windowEl, callback) {
      if (!windowEl) return;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) {
        windowEl.classList.add('d-none');
        if (typeof callback === 'function') callback();
        return;
      }

      window.gsap.to(windowEl, {
        autoAlpha: 0,
        scale: 0.88,
        y: 16,
        duration: 0.22,
        ease: 'power2.in',
        onComplete: () => {
          windowEl.classList.add('d-none');
          if (typeof callback === 'function') callback();
        },
      });
    },

    /**
     * Toast Slide-In from Right with Elastic Bounce
     */
    animateToastIn(toastEl) {
      if (!toastEl || typeof window.gsap === 'undefined') return;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) return;

      window.gsap.fromTo(
        toastEl,
        { x: 80, autoAlpha: 0, scale: 0.9 },
        { x: 0, autoAlpha: 1, scale: 1, duration: 0.42, ease: 'back.out(1.4)' }
      );
    },

    /**
     * Toast Dismiss Slide Out
     */
    animateToastOut(toastEl, onComplete) {
      if (!toastEl) return;

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced || typeof window.gsap === 'undefined') {
        if (typeof onComplete === 'function') onComplete();
        return;
      }

      window.gsap.to(toastEl, {
        x: 60,
        autoAlpha: 0,
        scale: 0.92,
        duration: 0.24,
        ease: 'power2.in',
        onComplete,
      });
    },

    /**
     * Recalculate ScrollTriggers after layout or dynamic content change
     */
    refreshScrollTriggers() {
      if (typeof window.ScrollTrigger !== 'undefined') {
        window.ScrollTrigger.refresh();
      }
    },
  };

  window.PWD.motion = PWDMotion;
  window.PWDMotion = PWDMotion;

  // Auto-init on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => PWDMotion.init());
  } else {
    PWDMotion.init();
  }
})();
