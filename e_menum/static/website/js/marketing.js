/**
 * E-Menum Marketing Pages JavaScript
 *
 * Provides:
 * - Smooth scroll for anchor links (GSAP ScrollToPlugin when available)
 * - Form validation helpers
 * - Pricing toggle (monthly/yearly)
 * - FAQ accordion (handled by Alpine.js inline)
 *
 * NOTE: Stats counter animation and scroll-reveal are now handled by
 *       homepage-animations.js via GSAP ScrollTrigger.
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================================
    // SMOOTH SCROLL — Anchor links (uses GSAP ScrollToPlugin if available)
    // ============================================================================

    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;

            var target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                if (typeof gsap !== 'undefined' && gsap.plugins && gsap.plugins.scrollTo) {
                    gsap.to(window, { duration: 0.8, scrollTo: { y: target, offsetY: 80 }, ease: 'power2.inOut' });
                } else {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });


    // ============================================================================
    // FORM VALIDATION HELPER
    // ============================================================================

    document.querySelectorAll('form[data-validate]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var isValid = true;
            var inputs = form.querySelectorAll('[required]');

            inputs.forEach(function (input) {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('border-red-500', 'ring-red-500');
                    input.classList.remove('border-gray-300', 'dark:border-gray-600');
                } else {
                    input.classList.remove('border-red-500', 'ring-red-500');
                    input.classList.add('border-gray-300', 'dark:border-gray-600');
                }
            });

            if (!isValid) {
                e.preventDefault();
                var firstError = form.querySelector('.border-red-500');
                if (firstError) firstError.focus();
            }
        });
    });

});
