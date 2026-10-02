/* login.js — deferred application script for the Vertex login/landing page */
(function () {
    'use strict';

    // ── DOM refs ──────────────────────────────────────────────────────────────
    var resetModalBackdrop, resetModal,
        sidebarBackdrop, sidebarPanel, menuToggleBtn,
        infoModalBackdrop, infoModalCard, infoModalTitle, infoModalBody;

    // ── Sidebar ───────────────────────────────────────────────────────────────
    function openSidebar() {
        sidebarBackdrop.classList.remove('hidden');
        sidebarPanel.classList.remove('-translate-x-full');
        sidebarPanel.classList.add('translate-x-0');
        sidebarBackdrop.setAttribute('aria-hidden', 'false');
        menuToggleBtn.setAttribute('aria-expanded', 'true');
    }

    function closeSidebar() {
        sidebarPanel.classList.remove('translate-x-0');
        sidebarPanel.classList.add('-translate-x-full');
        sidebarBackdrop.setAttribute('aria-hidden', 'true');
        menuToggleBtn.setAttribute('aria-expanded', 'false');
        setTimeout(function () {
            if (sidebarBackdrop.getAttribute('aria-hidden') === 'true') {
                sidebarBackdrop.classList.add('hidden');
            }
        }, 300);
    }

    // ── Info modal ────────────────────────────────────────────────────────────
    function openInfoModal(title, text) {
        infoModalTitle.textContent = title;
        infoModalBody.textContent = text;
        infoModalBackdrop.classList.remove('hidden');
        infoModalBackdrop.classList.add('flex');
        infoModalBackdrop.setAttribute('aria-hidden', 'false');
    }

    function closeInfoModal() {
        infoModalBackdrop.classList.remove('flex');
        infoModalBackdrop.classList.add('hidden');
        infoModalBackdrop.setAttribute('aria-hidden', 'true');
    }

    // ── Reset modal ───────────────────────────────────────────────────────────
    function openResetModal() {
        resetModalBackdrop.classList.remove('hidden');
        resetModalBackdrop.classList.add('flex');
        resetModalBackdrop.setAttribute('aria-hidden', 'false');
    }

    function closeResetModal() {
        resetModalBackdrop.classList.remove('flex');
        resetModalBackdrop.classList.add('hidden');
        resetModalBackdrop.setAttribute('aria-hidden', 'true');
    }

    // ── Login form ────────────────────────────────────────────────────────────
    function handleLogin(e) {
        e.preventDefault();
        document.getElementById('loadingOverlay').style.display = 'flex';
        setTimeout(function () {
            document.getElementById('loginForm').submit();
        }, 5000);
    }

    // ── Expose to global scope so inline onclick= attributes still work ───────
    window.openSidebar    = openSidebar;
    window.closeSidebar   = closeSidebar;
    window.openInfoModal  = openInfoModal;
    window.closeInfoModal = closeInfoModal;
    window.openResetModal = openResetModal;
    window.closeResetModal = closeResetModal;
    window.handleLogin    = handleLogin;

    // ── IntersectionObserver — scroll-reveal ──────────────────────────────────
    function initReveal() {
        var targets = document.querySelectorAll('.reveal');
        if (!targets.length) return;

        if (!('IntersectionObserver' in window)) {
            // Fallback for older browsers: show all immediately
            targets.forEach(function (el) { el.classList.add('visible'); });
            return;
        }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target); // fire once
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -48px 0px' });

        targets.forEach(function (el) { observer.observe(el); });
    }

    // ── Bootstrap on DOMContentLoaded ────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', function () {
        // Cache DOM refs
        resetModalBackdrop = document.getElementById('resetModalBackdrop');
        resetModal         = document.getElementById('resetModal');
        sidebarBackdrop    = document.getElementById('sidebarBackdrop');
        sidebarPanel       = document.getElementById('sidebarPanel');
        menuToggleBtn      = document.getElementById('menuToggleBtn');
        infoModalBackdrop  = document.getElementById('infoModalBackdrop');
        infoModalCard      = document.getElementById('infoModalCard');
        infoModalTitle     = document.getElementById('infoModalTitle');
        infoModalBody      = document.getElementById('infoModalBody');

        // Ensure sidebar starts closed
        closeSidebar();

        // Info-item click delegation
        document.querySelectorAll('.info-item').forEach(function (item) {
            item.addEventListener('click', function () {
                openInfoModal(
                    item.getAttribute('data-title') || 'Details',
                    item.getAttribute('data-info') || 'Information unavailable.'
                );
            });
        });

        // Close backdrop on outside-click
        sidebarBackdrop.addEventListener('click', function (event) {
            if (!sidebarPanel.contains(event.target)) closeSidebar();
        });
        infoModalBackdrop.addEventListener('click', function (event) {
            if (!infoModalCard.contains(event.target)) closeInfoModal();
        });
        resetModalBackdrop.addEventListener('click', function (event) {
            if (!resetModal.contains(event.target)) closeResetModal();
        });

        // Keyboard: Escape closes any open overlay
        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape') return;
            if (resetModalBackdrop.getAttribute('aria-hidden') === 'false') closeResetModal();
            if (sidebarBackdrop.getAttribute('aria-hidden') === 'false') closeSidebar();
            if (infoModalBackdrop.getAttribute('aria-hidden') === 'false') closeInfoModal();
        });

        // Scroll-reveal
        initReveal();
    });
}());
