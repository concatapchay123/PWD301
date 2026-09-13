/**
 * PWD301 — Online Course Management Platform
 * Shared UI Components & SVG Primitives
 * Functional Minimalism — No AI Slop
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};

  // Clean SVG Icons System (Feather/Lucide style, 16x16 / 20x20)
  const icons = {
    book: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>`,
    graduation: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>`,
    users: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`,
    user: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`,
    fileText: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`,
    checkCircle: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`,
    alertCircle: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
    alertTriangle: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
    clock: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`,
    lock: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`,
    unlock: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>`,
    shield: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`,
    activity: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>`,
    database: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>`,
    server: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`,
    sparkles: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.912 5.885L20 10.8l-4.756 3.662L16.824 20 12 16.326 7.176 20l1.58-5.538L4 10.8l6.088-1.915L12 3z"></path></svg>`,
    upload: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>`,
    download: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`,
    search: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`,
    plus: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`,
    edit: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`,
    trash: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`,
    bell: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>`,
    wifi: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>`,
    wifiOff: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"></path><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"></path><path d="M10.71 5.05A16 16 0 0 1 22.58 9"></path><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>`,
    refresh: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`,
    chevronRight: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`,
    arrowLeft: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>`,
    moreVertical: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>`,
    settings: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
    sun: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`,
    moon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`,
    x: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
    maximize2: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>`,
    send: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`,
    messageCircle: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>`,
    heart: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
    heartFill: `<svg width="18" height="18" viewBox="0 0 24 24" fill="#a435f0" stroke="#a435f0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
    star: `<svg width="14" height="14" viewBox="0 0 24 24" fill="#b4690e" stroke="#b4690e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`,
    play: `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="6 4 20 12 6 20 6 4"></polygon></svg>`,
    pause: `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>`,
    rotateCcw: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>`,
    rotateCw: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>`,
    volume2: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`,
    volumeX: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`,
    video: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>`,
    helpCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
    share: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>`,
    award: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg>`,
    code: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,
    layout: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>`,
    cpu: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>`,
    terminal: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>`
  };

  const components = {
    // Return SVG icon string
    icon(name) {
      return icons[name] || '';
    },

    // Page Header with single clear primary action
    pageHeader(options) {
      const { title, subtitle, breadcrumbs, primaryAction, secondaryActions } = options;
      
      let crumbsHtml = '';
      if (breadcrumbs && breadcrumbs.length > 0) {
        crumbsHtml = `
          <nav class="app-breadcrumbs" aria-label="Breadcrumb">
            ${breadcrumbs.map((b, idx) => {
              const isLast = idx === breadcrumbs.length - 1;
              return isLast 
                ? `<span>${b.label}</span>`
                : `<a href="${b.href}">${b.label}</a> <span class="crumb-sep">/</span>`;
            }).join(' ')}
          </nav>
        `;
      }

      return `
        <header class="page-header">
          <div class="page-header-content">
            ${crumbsHtml}
            <h1 class="page-title">${title}</h1>
            ${subtitle ? `<p class="page-header-subtitle">${subtitle}</p>` : ''}
          </div>
          <div class="page-header-actions">
            ${secondaryActions || ''}
            ${primaryAction ? `<div class="ms-1">${primaryAction}</div>` : ''}
          </div>
        </header>
      `;
    },

    // Colorful Icon Box
    iconBox(name, variant = 'primary') {
      const validVariants = ['primary', 'emerald', 'amber', 'violet', 'rose'];
      const v = validVariants.includes(variant) ? variant : 'primary';
      return `<div class="icon-box icon-box-${v}">${icons[name] || ''}</div>`;
    },

    // Hero Welcome Card with vibrant gradient
    heroWelcome(title, subtitle, actionHtml = '') {
      return `
        <div class="hero-welcome-card">
          <div>
            <h3 class="fw-bold mb-2">${title}</h3>
            <p class="m-0 text-white-50" style="font-size: 15.5px; line-height: 1.6; max-width: 680px;">${subtitle}</p>
          </div>
          ${actionHtml ? `<div class="ms-3">${actionHtml}</div>` : ''}
        </div>
      `;
    },

    // Metric / Stat card with colorful Icon Box
    statCard(label, value, context = '', iconName = '', variant = 'primary') {
      return `
        <div class="metric-card">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="metric-label">${label}</span>
            ${iconName ? this.iconBox(iconName, variant) : ''}
          </div>
          <div class="metric-value my-1">${value}</div>
          ${context ? `<div class="metric-context mt-1">${context}</div>` : ''}
        </div>
      `;
    },

    // Multi-step Wizard Stepper
    stepWizard(steps, currentStepIndex = 0) {
      return `
        <div class="step-wizard">
          ${steps.map((s, idx) => {
            let stateClass = '';
            if (idx === currentStepIndex) stateClass = 'active';
            else if (idx < currentStepIndex) stateClass = 'completed';

            const badgeContent = idx < currentStepIndex ? '✓' : (idx + 1);
            return `
              <div class="step-item ${stateClass}">
                <div class="step-badge">${badgeContent}</div>
                <span>${s.title}</span>
              </div>
              ${idx < steps.length - 1 ? `<div class="step-divider"></div>` : ''}
            `;
          }).join('')}
        </div>
      `;
    },

    // Status Badge
    badge(type, text) {
      const validTypes = ['success', 'warning', 'danger', 'info', 'neutral'];
      const badgeType = validTypes.includes(type) ? type : 'neutral';
      return `<span class="badge badge-${badgeType}"><span class="badge-dot"></span>${text}</span>`;
    },

    // Empty state
    emptyState(title, description, actionButtonHtml = '', iconName = 'book') {
      return `
        <div class="empty-state py-5">
          <div class="empty-state-icon mb-3">${icons[iconName] || icons.book}</div>
          <div class="empty-state-title mb-2">${title}</div>
          <p class="empty-state-desc mb-4" style="line-height: 1.6;">${description}</p>
          ${actionButtonHtml ? `<div class="mt-2">${actionButtonHtml}</div>` : ''}
        </div>
      `;
    },

    // Progress Bar
    progressBar(percent, isSuccess = false) {
      const clamped = Math.min(100, Math.max(0, percent));
      return `
        <div class="d-flex align-items-center gap-2" style="min-width: 120px;">
          <div class="progress-bar-container flex-grow-1">
            <div class="progress-bar-fill ${isSuccess ? 'success' : ''}" style="width: ${clamped}%;"></div>
          </div>
          <span class="text-caption" style="min-width: 32px; text-align: right;">${clamped}%</span>
        </div>
      `;
    },

    // Toast feedback notification - Displayed at top-right with slide-in from right animation
    showToast(message, type = 'info', duration = 4000) {
      let container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
      }

      const toast = document.createElement('div');
      const normalizedType = (type === 'error' ? 'danger' : (type || 'info'));
      toast.className = `app-toast toast-${normalizedType}`;
      toast.setAttribute('role', 'alert');
      toast.setAttribute('data-auto-dismiss', duration);
      
      let icon = icons.alertCircle;
      if (normalizedType === 'success') icon = icons.checkCircle;
      if (normalizedType === 'danger') icon = icons.alertTriangle;
      if (normalizedType === 'warning') icon = icons.alertTriangle;

      toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
        <button type="button" class="toast-close-btn" aria-label="Đóng">${icons.x}</button>
        <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
      `;

      container.prepend(toast);
      if (window.PWD && window.PWD.motion && typeof window.PWD.motion.animateToastIn === 'function') {
        window.PWD.motion.animateToastIn(toast);
      }
      this.bindToastEvents(toast, duration);
    },

    // Bind auto-dismiss, hover pause/resume, and close interaction
    bindToastEvents(toast, duration = 4000) {
      if (!toast || toast._hasToastEvents) return;
      toast._hasToastEvents = true;

      let remaining = duration;
      let startTime = Date.now();
      let timerId = null;

      const dismiss = () => {
        if (toast._isDismissing) return;
        toast._isDismissing = true;
        toast.classList.add('toast-hiding');
        if (window.PWD && window.PWD.motion && typeof window.PWD.motion.animateToastOut === 'function') {
          window.PWD.motion.animateToastOut(toast, () => {
            try { toast.remove(); } catch (e) {}
          });
        } else {
          setTimeout(() => {
            try { toast.remove(); } catch (e) {}
          }, 260);
        }
      };

      const startTimer = () => {
        startTime = Date.now();
        timerId = setTimeout(dismiss, remaining);
      };

      const pauseTimer = () => {
        clearTimeout(timerId);
        remaining -= (Date.now() - startTime);
        if (remaining < 800) remaining = 800;
      };

      startTimer();

      toast.addEventListener('mouseenter', pauseTimer);
      toast.addEventListener('mouseleave', startTimer);

      const closeBtn = toast.querySelector('.toast-close-btn');
      if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          clearTimeout(timerId);
          dismiss();
        });
      }
    },

    // Initialize all existing server-rendered toasts on the page
    initToasts() {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const toasts = container.querySelectorAll('.app-toast');
      toasts.forEach((toast) => {
        const duration = parseInt(toast.getAttribute('data-auto-dismiss') || '4000', 10);
        this.bindToastEvents(toast, duration);
      });
    },

    // FPT SVG Geometric Patterns (Matching FPT LMS Image 1)
    fptPatternSvg(patternType) {
      switch (patternType) {
        case 'emerald-grid':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#00a86b"/>
              <g opacity="0.22">
                <rect x="0" y="0" width="53" height="40" fill="#01472e"/>
                <rect x="106" y="0" width="54" height="40" fill="#01472e"/>
                <rect x="213" y="0" width="54" height="40" fill="#01472e"/>
                <rect x="53" y="40" width="53" height="40" fill="#01472e"/>
                <rect x="160" y="40" width="53" height="40" fill="#01472e"/>
                <rect x="267" y="40" width="53" height="40" fill="#01472e"/>
                <rect x="0" y="80" width="53" height="40" fill="#01472e"/>
                <rect x="106" y="80" width="54" height="40" fill="#01472e"/>
                <rect x="213" y="80" width="54" height="40" fill="#01472e"/>
                <rect x="53" y="120" width="53" height="40" fill="#01472e"/>
                <rect x="160" y="120" width="53" height="40" fill="#01472e"/>
                <rect x="267" y="120" width="53" height="40" fill="#01472e"/>
              </g>
              <g opacity="0.18">
                <rect x="53" y="0" width="53" height="40" fill="#ffffff"/>
                <rect x="160" y="0" width="53" height="40" fill="#ffffff"/>
                <rect x="267" y="0" width="53" height="40" fill="#ffffff"/>
                <rect x="0" y="40" width="53" height="40" fill="#ffffff"/>
                <rect x="106" y="40" width="54" height="40" fill="#ffffff"/>
                <rect x="213" y="40" width="54" height="40" fill="#ffffff"/>
                <rect x="53" y="80" width="53" height="40" fill="#ffffff"/>
                <rect x="160" y="80" width="53" height="40" fill="#ffffff"/>
                <rect x="267" y="80" width="53" height="40" fill="#ffffff"/>
                <rect x="0" y="120" width="53" height="40" fill="#ffffff"/>
                <rect x="106" y="120" width="54" height="40" fill="#ffffff"/>
                <rect x="213" y="120" width="54" height="40" fill="#ffffff"/>
              </g>
            </svg>
          `;
        case 'blue-rings':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#1976d2"/>
              <g stroke="#ffffff" stroke-width="4" fill="none" opacity="0.22">
                <circle cx="50" cy="80" r="20"/>
                <circle cx="50" cy="80" r="42"/>
                <circle cx="50" cy="80" r="66"/>
                <circle cx="130" cy="80" r="22"/>
                <circle cx="130" cy="80" r="46"/>
                <circle cx="210" cy="80" r="20"/>
                <circle cx="210" cy="80" r="42"/>
                <circle cx="210" cy="80" r="66"/>
                <circle cx="290" cy="80" r="24"/>
                <circle cx="290" cy="80" r="50"/>
              </g>
              <g fill="#ffffff" opacity="0.12">
                <circle cx="50" cy="80" r="10"/>
                <circle cx="130" cy="80" r="12"/>
                <circle cx="210" cy="80" r="10"/>
                <circle cx="290" cy="80" r="12"/>
              </g>
            </svg>
          `;
        case 'grey-tartan':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#d1d5db"/>
              <rect x="0" y="25" width="320" height="16" fill="#9ca3af" opacity="0.4"/>
              <rect x="0" y="80" width="320" height="26" fill="#6b7280" opacity="0.35"/>
              <rect x="0" y="125" width="320" height="12" fill="#9ca3af" opacity="0.45"/>
              <rect x="45" y="0" width="18" height="160" fill="#9ca3af" opacity="0.4"/>
              <rect x="130" y="0" width="24" height="160" fill="#6b7280" opacity="0.35"/>
              <rect x="230" y="0" width="16" height="160" fill="#9ca3af" opacity="0.45"/>
              <rect x="270" y="0" width="8" height="160" fill="#4b5563" opacity="0.3"/>
            </svg>
          `;
        case 'pink-polygon':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#f43f5e"/>
              <polygon points="160,10 230,50 230,120 160,155 90,120 90,50" fill="#ffffff" opacity="0.12"/>
              <polygon points="80,10 150,50 150,120 80,155 10,120 10,50" fill="#ffffff" opacity="0.18"/>
              <polygon points="240,10 310,50 310,120 240,155 170,120 170,50" fill="#ffffff" opacity="0.14"/>
              <polygon points="160,50 200,75 200,115 160,135 120,115 120,75" fill="#ffffff" opacity="0.22"/>
              <line x1="160" y1="10" x2="160" y2="155" stroke="#ffffff" stroke-width="2" opacity="0.25"/>
              <line x1="90" y1="50" x2="230" y2="120" stroke="#ffffff" stroke-width="2" opacity="0.25"/>
              <line x1="90" y1="120" x2="230" y2="50" stroke="#ffffff" stroke-width="2" opacity="0.25"/>
            </svg>
          `;
        case 'green-mosaic':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#059669"/>
              <polygon points="160,0 260,80 160,160 60,80" fill="#ffffff" opacity="0.15"/>
              <polygon points="260,0 360,80 260,160 160,80" fill="#ffffff" opacity="0.1"/>
              <polygon points="60,0 160,80 60,160 -40,80" fill="#ffffff" opacity="0.2"/>
              <circle cx="160" cy="80" r="45" fill="none" stroke="#ffffff" stroke-width="3" opacity="0.25"/>
            </svg>
          `;
        case 'slate-tartan':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#94a3b8"/>
              <rect x="0" y="20" width="320" height="18" fill="#475569" opacity="0.3"/>
              <rect x="0" y="75" width="320" height="28" fill="#334155" opacity="0.35"/>
              <rect x="0" y="125" width="320" height="14" fill="#475569" opacity="0.3"/>
              <rect x="50" y="0" width="20" height="160" fill="#475569" opacity="0.3"/>
              <rect x="140" y="0" width="26" height="160" fill="#334155" opacity="0.35"/>
              <rect x="240" y="0" width="18" height="160" fill="#475569" opacity="0.3"/>
            </svg>
          `;
        case 'cyan-diamonds':
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#0284c7"/>
              <g stroke="#ffffff" stroke-width="2" fill="none" opacity="0.2">
                <line x1="-40" y1="0" x2="160" y2="200"/>
                <line x1="20" y1="0" x2="220" y2="200"/>
                <line x1="80" y1="0" x2="280" y2="200"/>
                <line x1="140" y1="0" x2="340" y2="200"/>
                <line x1="200" y1="0" x2="400" y2="200"/>
                <line x1="160" y1="0" x2="-40" y2="200"/>
                <line x1="220" y1="0" x2="20" y2="200"/>
                <line x1="280" y1="0" x2="80" y2="200"/>
                <line x1="340" y1="0" x2="140" y2="200"/>
                <line x1="400" y1="0" x2="200" y2="200"/>
              </g>
            </svg>
          `;
        default:
          return `
            <svg class="fpt-banner-svg" width="100%" height="100%" viewBox="0 0 320 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="160" fill="#3b82f6"/>
              <circle cx="80" cy="80" r="60" fill="#ffffff" opacity="0.15"/>
              <circle cx="240" cy="80" r="60" fill="#ffffff" opacity="0.15"/>
            </svg>
          `;
      }
    },

    // Unified FPT LMS + Udemy Hybrid Course Card (Combining Image 1 & Image 2)
    renderCourseCard(course, options = {}) {
      const link = options.targetLink || `#/student/course/${course.id}`;
      const isEnrolled = course.enrolled;

      return `
        <div class="col-md-6 col-lg-4 fpt-udemy-card-col mb-4" data-category="${course.category}" data-query="${course.title.toLowerCase()} ${course.code.toLowerCase()}">
          <div class="fpt-udemy-card">
            <!-- 1. Top Banner: FPT Geometric SVG Pattern + FPT Orange Badge + Udemy Premium & Wishlist -->
            <a href="${link}" class="fpt-udemy-banner text-decoration-none">
              ${this.fptPatternSvg(course.fptPattern || 'emerald-grid')}
              
              <!-- FPT Orange Pill Badge (Image 1 reference) -->
              <div class="fpt-banner-pill" title="${course.code} - ${course.title}">
                ${course.code} - ${course.title}
              </div>

              <!-- Udemy Premium Badge & Wishlist (Image 2 reference) -->
              <div class="fpt-banner-top-right">
                <span class="udemy-badge-premium">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="white" stroke="white"><path d="M12 2l2.4 7.2h7.6l-6.1 4.5 2.3 7.3-6.2-4.6-6.2 4.6 2.3-7.3-6.1-4.5h7.6z"/></svg>
                  Cao cấp
                </span>
                <button type="button" class="udemy-wishlist-btn ${course.wishlisted ? 'active' : ''}" onclick="PWD.components.handleToggleWishlist('${course.id}', event)" title="${course.wishlisted ? 'Đã lưu yêu thích' : 'Lưu vào yêu thích'}">
                  ${course.wishlisted ? icons.heartFill : icons.heart}
                </button>
              </div>
            </a>

            <!-- 2. Content Body: Title, FPT Instructor, Udemy Badges, Ratings, Price & Action -->
            <div class="fpt-udemy-body">
              <a href="${link}" class="text-decoration-none">
                <h5 class="fpt-udemy-title" title="${course.title}">${course.title}</h5>
              </a>

              <!-- FPT-Style Code & Instructor Row (Image 1 reference) -->
              <div class="fpt-udemy-instructor">
                <span class="fpt-code-prefix">${course.code}</span> - ${course.instructorName}
              </div>

              <!-- Udemy Badges Row (Image 2 reference) -->
              <div class="d-flex align-items-center gap-2 my-2 flex-wrap">
                ${course.bestseller ? '<span class="udemy-badge-bestseller">Bán chạy nhất</span>' : ''}
                <span class="udemy-badge-tag">Khóa học</span>
                <span class="badge badge-neutral" style="font-size: 11px;">${course.category}</span>
              </div>

              <!-- Udemy Rating Row (Image 2 reference) -->
              <div class="udemy-rating-wrap">
                <span class="udemy-rating-num">${course.rating || '4.8'}</span>
                <span class="udemy-stars">${icons.star}</span>
                <span class="udemy-rating-count">(${course.ratingCount || '18.420 xếp hạng'})</span>
                <span class="text-caption text-muted ms-auto">${course.lessonsCount} bài</span>
              </div>

              ${isEnrolled && course.progress > 0 ? `
                <!-- Progress bar for enrolled courses -->
                <div class="my-2">
                  <div class="d-flex justify-content-between text-caption mb-1">
                    <span class="text-muted">Tiến độ học tập</span>
                    <span class="fw-semibold" style="color: #a435f0;">${course.progress}%</span>
                  </div>
                  <div class="progress" style="height: 6px; border-radius: 999px; background: rgba(164, 53, 240, 0.15);">
                    <div class="progress-bar" role="progressbar" style="width: ${course.progress}%; background: #a435f0; border-radius: 999px;"></div>
                  </div>
                </div>
              ` : ''}

              <!-- Card Footer: Pricing + Action Button -->
              <div class="fpt-udemy-footer">
                <div class="udemy-price-wrap">
                  <span class="udemy-current-price">${course.price || '249.000 đ'}</span>
                  <span class="udemy-old-price">${course.originalPrice || '1.580.000 đ'}</span>
                </div>
                <a href="${link}" class="btn udemy-btn-cart">
                  ${isEnrolled ? 'Vào học' : 'Thêm vào giỏ'}
                </a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // Aliases for backward compatibility
    renderFptCourseCard(course, options = {}) {
      return this.renderCourseCard(course, options);
    },

    renderUdemyCourseCard(course, options = {}) {
      return this.renderCourseCard(course, options);
    },

    renderViewModeSwitcher() {
      return ''; // Removed as requested; system now uses unified FPT + Udemy hybrid cards
    },

    // Wishlist Toggle Handler
    handleToggleWishlist(courseId, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      const isSaved = window.PWD.store.toggleWishlist(courseId);
      const course = window.PWD.store.state.courses.find(c => c.id === courseId);
      const msg = isSaved 
        ? `Đã thêm "${course ? course.title : 'Khóa học'}" vào danh sách yêu thích!`
        : `Đã xóa khỏi danh sách yêu thích.`;
      this.showToast(msg, 'success');

      // Update button visual directly if present
      if (event && event.currentTarget) {
        const btn = event.currentTarget;
        if (isSaved) {
          btn.classList.add('active');
          btn.innerHTML = icons.heartFill;
        } else {
          btn.classList.remove('active');
          btn.innerHTML = icons.heart;
        }
      }
    },

    // Confirmation Modal for Destructive / Sensitive Actions
    openConfirmModal(options) {
      const {
        title = 'Xác nhận thao tác',
        message = 'Bạn có chắc chắn muốn thực hiện thao tác này?',
        confirmText = 'Xác nhận',
        confirmBtnClass = 'btn-danger',
        onConfirm = () => {}
      } = options;

      let modalEl = document.getElementById('app-confirm-modal');
      if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.id = 'app-confirm-modal';
        modalEl.className = 'modal fade';
        modalEl.tabIndex = -1;
        modalEl.innerHTML = `
          <div class="modal-dialog modal-dialog-centered" style="max-width: 440px;">
            <div class="modal-content" style="border: 1px solid var(--slate-200); border-radius: var(--radius-md);">
              <div class="modal-header" style="border-bottom: 1px solid var(--slate-200); padding: var(--space-3) var(--space-4);">
                <h5 class="modal-title sub-title" id="app-confirm-title" style="margin:0;"></h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Đóng"></button>
              </div>
              <div class="modal-body" style="padding: var(--space-4); font-size: var(--font-body);">
                <p id="app-confirm-body" style="margin:0;"></p>
              </div>
              <div class="modal-footer" style="border-top: 1px solid var(--slate-200); padding: var(--space-3) var(--space-4); background: var(--slate-50);">
                <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Hủy</button>
                <button type="button" class="btn btn-sm" id="app-confirm-btn"></button>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(modalEl);
      }

      document.getElementById('app-confirm-title').textContent = title;
      document.getElementById('app-confirm-body').innerHTML = message;
      
      const confirmBtn = document.getElementById('app-confirm-btn');
      confirmBtn.className = `btn btn-sm ${confirmBtnClass}`;
      confirmBtn.textContent = confirmText;

      const bsModal = new bootstrap.Modal(modalEl);
      
      const clickHandler = () => {
        confirmBtn.removeEventListener('click', clickHandler);
        bsModal.hide();
        onConfirm();
      };
      
      // Clean up previous listeners
      const newConfirmBtn = confirmBtn.cloneNode(true);
      confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
      newConfirmBtn.addEventListener('click', clickHandler);

      bsModal.show();
    },

    // Defensive UX: High-impact Admin Sensitive Action Modal
    // Enforces: re-authentication password + exact phrase match + mandatory reason
    openSensitiveActionModal(options) {
      const {
        title = 'Thao tác bảo mật cấp quản trị',
        actionDescription = 'Thao tác này có ảnh hưởng lớn tới tài nguyên hệ thống.',
        requiredPhrase = 'XÁC NHẬN THỰC HIỆN',
        confirmButtonText = 'Thực hiện thao tác',
        onConfirm = (data) => {}
      } = options;

      let modalEl = document.getElementById('app-sensitive-modal');
      if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.id = 'app-sensitive-modal';
        modalEl.className = 'modal fade';
        modalEl.tabIndex = -1;
        modalEl.innerHTML = `
          <div class="modal-dialog modal-dialog-centered" style="max-width: 480px;">
            <div class="modal-content" style="border: 1px solid var(--color-danger-border); border-radius: var(--radius-md);">
              <div class="modal-header" style="background: var(--color-danger-bg); border-bottom: 1px solid var(--color-danger-border); padding: var(--space-3) var(--space-4);">
                <div class="d-flex align-items-center gap-2">
                  <span style="color: var(--color-danger);">${icons.alertTriangle}</span>
                  <h5 class="modal-title sub-title" id="sensitive-modal-title" style="margin:0; color: var(--color-danger);"></h5>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Đóng"></button>
              </div>
              <div class="modal-body" style="padding: var(--space-4); font-size: var(--font-body);">
                <div class="alert-card alert-card-danger mb-3" id="sensitive-modal-desc"></div>

                <div class="form-group mb-3">
                  <label class="form-label">Mật khẩu quản trị viên xác thực lại <span class="required">*</span></label>
                  <input type="password" class="form-control form-control-sm" id="sensitive-password" placeholder="Nhập mật khẩu xác thực (demo: bất kỳ)">
                  <div class="form-hint">Mô phỏng xác thực lại danh tính quản trị viên trước tác vụ nhạy cảm.</div>
                </div>

                <div class="form-group mb-3">
                  <label class="form-label">Nhập chính xác cụm từ: <code id="sensitive-phrase-target" class="text-danger fw-bold"></code> <span class="required">*</span></label>
                  <input type="text" class="form-control form-control-sm" id="sensitive-phrase-input" placeholder="Gõ đúng cụm từ trên">
                </div>

                <div class="form-group mb-0">
                  <label class="form-label">Lý do thực hiện bắt buộc <span class="required">*</span></label>
                  <textarea class="form-control form-control-sm" id="sensitive-reason" rows="2" placeholder="Ghi rõ căn cứ và lý do thực hiện..."></textarea>
                  <div class="form-hint">Lý do sẽ được ghi cố định vào Nhật ký kiểm toán (Audit Log).</div>
                </div>
              </div>
              <div class="modal-footer" style="border-top: 1px solid var(--slate-200); padding: var(--space-3) var(--space-4); background: var(--slate-50);">
                <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Hủy bỏ</button>
                <button type="button" class="btn btn-danger btn-sm" id="sensitive-submit-btn" disabled>
                  ${confirmButtonText}
                </button>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(modalEl);
      }

      document.getElementById('sensitive-modal-title').textContent = title;
      document.getElementById('sensitive-modal-desc').innerHTML = actionDescription;
      document.getElementById('sensitive-phrase-target').textContent = requiredPhrase;

      const pwdInput = document.getElementById('sensitive-password');
      const phraseInput = document.getElementById('sensitive-phrase-input');
      const reasonInput = document.getElementById('sensitive-reason');
      const submitBtn = document.getElementById('sensitive-submit-btn');

      pwdInput.value = '';
      phraseInput.value = '';
      reasonInput.value = '';
      submitBtn.disabled = true;

      function checkValidity() {
        const hasPwd = pwdInput.value.trim().length > 0;
        const phraseMatches = phraseInput.value.trim() === requiredPhrase.trim();
        const hasReason = reasonInput.value.trim().length >= 5;
        submitBtn.disabled = !(hasPwd && phraseMatches && hasReason);
      }

      pwdInput.oninput = checkValidity;
      phraseInput.oninput = checkValidity;
      reasonInput.oninput = checkValidity;

      const bsModal = new bootstrap.Modal(modalEl);

      submitBtn.onclick = () => {
        const reason = reasonInput.value.trim();
        bsModal.hide();
        onConfirm({ reason });
      };

      bsModal.show();
    }
  };

  window.PWD.components = components;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => components.initToasts());
  } else {
    components.initToasts();
  }
})();
