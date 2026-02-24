/**
 * E-Menum Marketing Pages JavaScript
 *
 * Provides:
 * - Stats counter animation (IntersectionObserver)
 * - Smooth scroll for anchor links
 * - Form validation helpers
 * - Pricing toggle (monthly/yearly)
 * - FAQ accordion (handled by Alpine.js inline)
 */

'use strict';

// ============================================================================
// STATS COUNTER — Animate numbers when scrolled into view
// ============================================================================

document.addEventListener('DOMContentLoaded', function () {

    /**
     * Animate a number from 0 to target.
     * @param {HTMLElement} el - Element containing `data-target` attribute.
     * @param {number} duration - Animation duration in ms.
     */
    function animateCounter(el, duration) {
        const target = parseInt(el.getAttribute('data-target'), 10);
        const suffix = el.getAttribute('data-suffix') || '';
        const prefix = el.getAttribute('data-prefix') || '';
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(eased * target);

            el.textContent = prefix + current.toLocaleString('tr-TR') + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = prefix + target.toLocaleString('tr-TR') + suffix;
            }
        }

        requestAnimationFrame(update);
    }

    // Observe all counter elements
    const counters = document.querySelectorAll('[data-counter]');
    if (counters.length > 0) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    animateCounter(entry.target, 2000);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        counters.forEach(function (el) { observer.observe(el); });
    }


    // ============================================================================
    // SCROLL REVEAL — Fade in elements on scroll
    // ============================================================================

    const reveals = document.querySelectorAll('[data-reveal]');
    if (reveals.length > 0 && 'IntersectionObserver' in window) {
        var revealedSet = new Set();

        var revealObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                    entry.target.style.opacity = '1';
                    revealedSet.add(entry.target);
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.01, rootMargin: '0px 0px 100px 0px' });

        reveals.forEach(function (el) {
            el.style.opacity = '0';
            el.style.transition = 'opacity 0.6s ease-out';
            revealObserver.observe(el);
        });

        // Fallback: reveal all elements after 2s if observer hasn't fired
        setTimeout(function () {
            reveals.forEach(function (el) {
                if (!revealedSet.has(el)) {
                    el.style.opacity = '1';
                }
            });
        }, 2000);
    }


    // ============================================================================
    // SMOOTH SCROLL — Anchor links
    // ============================================================================

    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;

            var target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
