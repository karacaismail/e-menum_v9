/* ═══════════════════════════════════════════════════════════════
   E-MENUM HOMEPAGE ANIMATIONS — Master GSAP ScrollTrigger Controller

   Orchestrates all scroll-driven animations for the enterprise homepage.
   Each section has its own init method for clean separation.

   Dependencies:
     - GSAP 3.12.5 core
     - GSAP ScrollTrigger plugin
     - GSAP ScrollToPlugin (smooth anchor scroll)

   Respects prefers-reduced-motion.
   ═══════════════════════════════════════════════════════════════ */

'use strict';

(function () {
  // ────────────────────────────────────────────────────────────
  // UTILITY: Split text into word spans for GSAP animation
  // ────────────────────────────────────────────────────────────
  function splitTextIntoWords(el) {
    if (!el || el.dataset.split === 'done') return [];
    var text = el.textContent.trim();
    if (!text) return [];
    var words = text.split(/\s+/);
    el.innerHTML = words.map(function (w) {
      return '<span class="hw"><span class="hw-inner">' + w + '</span></span>';
    }).join(' ');
    el.dataset.split = 'done';
    return el.querySelectorAll('.hw-inner');
  }

  // ────────────────────────────────────────────────────────────
  // UTILITY: GSAP counter animation
  // ────────────────────────────────────────────────────────────
  function animateGSAPCounter(el, duration) {
    var target = parseInt(el.getAttribute('data-target'), 10);
    if (isNaN(target)) return;
    var suffix = el.getAttribute('data-suffix') || '';
    var prefix = el.getAttribute('data-prefix') || '';
    var obj = { val: 0 };
    gsap.to(obj, {
      val: target,
      duration: duration || 2,
      ease: 'power2.out',
      snap: { val: 1 },
      onUpdate: function () {
        el.textContent = prefix + obj.val.toLocaleString('tr-TR') + suffix;
      }
    });
  }

  // ────────────────────────────────────────────────────────────
  // MAIN CONTROLLER
  // ────────────────────────────────────────────────────────────
  var HomepageAnimations = {

    reducedMotion: false,

    init: function () {
      this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        return;
      }
      gsap.registerPlugin(ScrollTrigger);

      if (this.reducedMotion) {
        // Show all elements immediately, no animation
        document.querySelectorAll('[data-reveal]').forEach(function (el) {
          el.style.opacity = '1';
        });
        return;
      }

      // Initialize section animations
      this.initScrollReveal();
      this.initTrustBar();
      this.initBeforeAfter();
      this.initBentoGrid();
      this.initROIImpact();
      this.initHowItWorks();
      this.initStats();
      this.initTestimonials();
      this.initPricing();
      this.initFAQ();
      this.initFinalCTA();
      this.initInteractiveDemo();

      // Refresh on resize (debounced)
      var resizeTimer;
      window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
          ScrollTrigger.refresh();
        }, 250);
      });
    },

    // ──────────────────────────────────────────────────────────
    // GLOBAL SCROLL REVEAL — replaces IntersectionObserver
    // ──────────────────────────────────────────────────────────
    initScrollReveal: function () {
      var els = gsap.utils.toArray('[data-reveal]');
      if (!els.length) return;

      // Set initial state
      gsap.set(els, { opacity: 0, y: 30 });

      ScrollTrigger.batch(els, {
        onEnter: function (batch) {
          gsap.to(batch, {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: 'power3.out',
            stagger: 0.1,
            overwrite: true
          });
        },
        start: 'top 88%',
        once: true
      });
    },

    // ──────────────────────────────────────────────────────────
    // TRUST BAR — Counter animation + badge stagger
    // ──────────────────────────────────────────────────────────
    initTrustBar: function () {
      var section = document.querySelector('.trust-bar-section');
      if (!section) return;

      var badges = gsap.utils.toArray(section.querySelectorAll('.trust-badge-item'));
      if (badges.length) {
        gsap.set(badges, { opacity: 0, y: 20 });
        ScrollTrigger.batch(badges, {
          onEnter: function (batch) {
            gsap.to(batch, {
              opacity: 1, y: 0,
              duration: 0.5, stagger: 0.08,
              ease: 'power2.out', overwrite: true
            });
          },
          start: 'top 85%',
          once: true
        });
      }

      // Animated counters
      var counters = section.querySelectorAll('[data-counter]');
      counters.forEach(function (el) {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 85%',
          once: true,
          onEnter: function () {
            animateGSAPCounter(el, 2);
          }
        });
      });
    },

    // ──────────────────────────────────────────────────────────
    // BEFORE / AFTER — Problem → Solution comparison
    // ──────────────────────────────────────────────────────────
    initBeforeAfter: function () {
      var section = document.querySelector('.before-after-section');
      if (!section) return;

      // Divider line draw
      var divider = section.querySelector('.ba-divider-line');
      if (divider) {
        gsap.set(divider, { scaleY: 0, transformOrigin: 'top center' });
        ScrollTrigger.create({
          trigger: section,
          start: 'top 70%',
          once: true,
          onEnter: function () {
            gsap.to(divider, { scaleY: 1, duration: 0.8, ease: 'power2.inOut' });
          }
        });
      }

      // Problem items from left
      var problems = gsap.utils.toArray(section.querySelectorAll('.ba-problem-item'));
      if (problems.length) {
        gsap.set(problems, { opacity: 0, x: -30, rotation: -1 });
        ScrollTrigger.create({
          trigger: section,
          start: 'top 65%',
          once: true,
          onEnter: function () {
            gsap.to(problems, {
              opacity: 1, x: 0, rotation: 0,
              duration: 0.6, stagger: 0.12, ease: 'power2.out'
            });
          }
        });
      }

      // Solution items from right
      var solutions = gsap.utils.toArray(section.querySelectorAll('.ba-solution-item'));
      if (solutions.length) {
        gsap.set(solutions, { opacity: 0, x: 30 });
        ScrollTrigger.create({
          trigger: section,
          start: 'top 65%',
          once: true,
          onEnter: function () {
            gsap.to(solutions, {
              opacity: 1, x: 0,
              duration: 0.6, stagger: 0.12, ease: 'power2.out',
              delay: 0.3
            });
          }
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // INTERACTIVE DEMO — Parallax entrance
    // ──────────────────────────────────────────────────────────
    initInteractiveDemo: function () {
      var section = document.querySelector('.interactive-demo-section');
      if (!section) return;

      var browser = section.querySelector('.demo-browser-frame');
      var phone = section.querySelector('.demo-phone-frame');

      if (browser) {
        gsap.set(browser, { opacity: 0, y: 60 });
        ScrollTrigger.create({
          trigger: section,
          start: 'top 75%',
          once: true,
          onEnter: function () {
            gsap.to(browser, { opacity: 1, y: 0, duration: 0.9, ease: 'power3.out' });
          }
        });
      }

      if (phone) {
        gsap.set(phone, { opacity: 0, y: 40, scale: 0.95 });
        ScrollTrigger.create({
          trigger: section,
          start: 'top 70%',
          once: true,
          onEnter: function () {
            gsap.to(phone, {
              opacity: 1, y: 0, scale: 1,
              duration: 0.8, ease: 'power3.out', delay: 0.3
            });
          }
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // BENTO GRID — Staggered card entrance with micro-anims
    // ──────────────────────────────────────────────────────────
    initBentoGrid: function () {
      var section = document.querySelector('.bento-section');
      if (!section) return;

      var cards = gsap.utils.toArray(section.querySelectorAll('.bento-card'));
      if (!cards.length) return;

      gsap.set(cards, { opacity: 0, y: 40, scale: 0.95 });

      ScrollTrigger.batch(cards, {
        onEnter: function (batch) {
          gsap.to(batch, {
            opacity: 1, y: 0, scale: 1,
            duration: 0.6, stagger: 0.08,
            ease: 'power3.out', overwrite: true
          });
        },
        start: 'top 85%',
        once: true
      });

      // Micro-animations inside cards (triggered when card visible)
      cards.forEach(function (card) {
        var bars = gsap.utils.toArray(card.querySelectorAll('.bento-micro-bar'));
        if (bars.length) {
          gsap.set(bars, { scaleY: 0, transformOrigin: 'bottom' });
          ScrollTrigger.create({
            trigger: card,
            start: 'top 80%',
            once: true,
            onEnter: function () {
              gsap.to(bars, {
                scaleY: 1, duration: 0.5,
                stagger: 0.06, ease: 'back.out(1.7)', delay: 0.3
              });
            }
          });
        }
      });
    },

    // ──────────────────────────────────────────────────────────
    // ROI IMPACT — Counter cards + bar graph
    // ──────────────────────────────────────────────────────────
    initROIImpact: function () {
      var section = document.querySelector('.roi-section');
      if (!section) return;

      // Counter cards
      var counters = section.querySelectorAll('[data-counter]');
      counters.forEach(function (el) {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 85%',
          once: true,
          onEnter: function () {
            animateGSAPCounter(el, 2);
          }
        });
      });

      // Bar graph animation
      var bars = gsap.utils.toArray(section.querySelectorAll('.roi-bar'));
      if (bars.length) {
        gsap.set(bars, { scaleY: 0, transformOrigin: 'bottom center' });
        ScrollTrigger.create({
          trigger: section.querySelector('.roi-graph'),
          start: 'top 80%',
          once: true,
          onEnter: function () {
            gsap.to(bars, {
              scaleY: 1, duration: 0.8,
              stagger: 0.15, ease: 'back.out(1.4)'
            });
          }
        });
      }

      // Card entrance
      var cards = gsap.utils.toArray(section.querySelectorAll('.roi-card'));
      if (cards.length) {
        gsap.set(cards, { opacity: 0, y: 30 });
        ScrollTrigger.batch(cards, {
          onEnter: function (batch) {
            gsap.to(batch, {
              opacity: 1, y: 0,
              duration: 0.6, stagger: 0.12, ease: 'power2.out'
            });
          },
          start: 'top 85%',
          once: true
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // HOW IT WORKS — Scroll-driven vertical timeline
    // ──────────────────────────────────────────────────────────
    initHowItWorks: function () {
      var section = document.querySelector('.hiw-section');
      if (!section) return;

      // Timeline line draw via scrub
      var line = section.querySelector('.hiw-timeline-line');
      if (line) {
        gsap.set(line, { scaleY: 0, transformOrigin: 'top center' });
        gsap.to(line, {
          scaleY: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: section,
            start: 'top 60%',
            end: 'bottom 70%',
            scrub: 1
          }
        });
      }

      // Steps: alternating left/right entrance
      var steps = gsap.utils.toArray(section.querySelectorAll('.hiw-step'));
      steps.forEach(function (step, i) {
        var xDir = i % 2 === 0 ? -40 : 40;
        gsap.set(step, { opacity: 0, x: xDir });

        ScrollTrigger.create({
          trigger: step,
          start: 'top 80%',
          once: true,
          onEnter: function () {
            gsap.to(step, {
              opacity: 1, x: 0,
              duration: 0.7, ease: 'power3.out'
            });
          }
        });

        // Step circle fill
        var circle = step.querySelector('.hiw-step-circle');
        if (circle) {
          gsap.set(circle, { scale: 0.5, opacity: 0.3 });
          ScrollTrigger.create({
            trigger: step,
            start: 'top 75%',
            once: true,
            onEnter: function () {
              gsap.to(circle, {
                scale: 1, opacity: 1,
                duration: 0.5, ease: 'back.out(2)'
              });
            }
          });
        }

        // Mockup scale-up
        var mockup = step.querySelector('.hiw-mockup');
        if (mockup) {
          gsap.set(mockup, { scale: 0.85, opacity: 0 });
          ScrollTrigger.create({
            trigger: step,
            start: 'top 70%',
            once: true,
            onEnter: function () {
              gsap.to(mockup, {
                scale: 1, opacity: 1,
                duration: 0.7, ease: 'power2.out', delay: 0.2
              });
            }
          });
        }
      });
    },

    // ──────────────────────────────────────────────────────────
    // STATS COUNTER — GSAP-powered counter animation
    // ──────────────────────────────────────────────────────────
    initStats: function () {
      var section = document.querySelector('.stats-section');
      if (!section) return;

      var counters = section.querySelectorAll('[data-counter]');
      counters.forEach(function (el) {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 85%',
          once: true,
          onEnter: function () {
            animateGSAPCounter(el, 2);
          }
        });
      });

      // Stat cards stagger entrance
      var cards = gsap.utils.toArray(section.querySelectorAll('.stat-card'));
      if (cards.length) {
        gsap.set(cards, { opacity: 0, y: 30 });
        ScrollTrigger.batch(cards, {
          onEnter: function (batch) {
            gsap.to(batch, {
              opacity: 1, y: 0,
              duration: 0.5, stagger: 0.1, ease: 'power2.out'
            });
          },
          start: 'top 85%',
          once: true
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // TESTIMONIALS — Featured quote + carousel entrance
    // ──────────────────────────────────────────────────────────
    initTestimonials: function () {
      var section = document.querySelector('.testimonials-section');
      if (!section) return;

      // Quote mark elastic entrance
      var quoteMark = section.querySelector('.testimonial-quote-mark');
      if (quoteMark) {
        gsap.set(quoteMark, { scale: 0, opacity: 0 });
        ScrollTrigger.create({
          trigger: section,
          start: 'top 75%',
          once: true,
          onEnter: function () {
            gsap.to(quoteMark, {
              scale: 1, opacity: 1,
              duration: 0.8, ease: 'elastic.out(1, 0.3)'
            });
          }
        });
      }

      // Featured quote text word-by-word reveal
      var quoteText = section.querySelector('.testimonial-featured-text');
      if (quoteText) {
        var words = splitTextIntoWords(quoteText);
        if (words.length) {
          gsap.set(words, { opacity: 0, y: 20 });
          ScrollTrigger.create({
            trigger: quoteText,
            start: 'top 80%',
            once: true,
            onEnter: function () {
              gsap.to(words, {
                opacity: 1, y: 0,
                duration: 0.4, stagger: 0.04, ease: 'power2.out'
              });
            }
          });
        }
      }

      // Cards stagger
      var cards = gsap.utils.toArray(section.querySelectorAll('.testimonial-card'));
      if (cards.length) {
        gsap.set(cards, { opacity: 0, y: 30 });
        ScrollTrigger.batch(cards, {
          onEnter: function (batch) {
            gsap.to(batch, {
              opacity: 1, y: 0,
              duration: 0.5, stagger: 0.1, ease: 'power2.out'
            });
          },
          start: 'top 85%',
          once: true
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // PRICING — ScrollTrigger stagger + spotlight
    // ──────────────────────────────────────────────────────────
    initPricing: function () {
      var section = document.querySelector('.pricing-section');
      if (!section) return;

      var cards = gsap.utils.toArray(section.querySelectorAll('.pricing-card'));
      if (cards.length) {
        gsap.set(cards, { opacity: 0, y: 40, scale: 0.96 });
        ScrollTrigger.batch(cards, {
          onEnter: function (batch) {
            gsap.to(batch, {
              opacity: 1, y: 0, scale: 1,
              duration: 0.6, stagger: 0.12,
              ease: 'power3.out', overwrite: true
            });
          },
          start: 'top 85%',
          once: true
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // FAQ — Section heading + items stagger
    // ──────────────────────────────────────────────────────────
    initFAQ: function () {
      var section = document.querySelector('.faq-section');
      if (!section) return;

      var items = gsap.utils.toArray(section.querySelectorAll('.faq-item'));
      if (items.length) {
        gsap.set(items, { opacity: 0, y: 20 });
        ScrollTrigger.batch(items, {
          onEnter: function (batch) {
            gsap.to(batch, {
              opacity: 1, y: 0,
              duration: 0.5, stagger: 0.08, ease: 'power2.out'
            });
          },
          start: 'top 85%',
          once: true
        });
      }
    },

    // ──────────────────────────────────────────────────────────
    // FINAL CTA — Parallax zoom + counter
    // ──────────────────────────────────────────────────────────
    initFinalCTA: function () {
      var section = document.querySelector('.cta-final-section');
      if (!section) return;

      // Parallax zoom-in on scroll
      var inner = section.querySelector('.cta-inner');
      if (inner) {
        gsap.fromTo(inner,
          { scale: 1.04, opacity: 0.7 },
          {
            scale: 1, opacity: 1,
            ease: 'none',
            scrollTrigger: {
              trigger: section,
              start: 'top 90%',
              end: 'top 40%',
              scrub: 1
            }
          }
        );
      }
    }
  };

  // ────────────────────────────────────────────────────────────
  // BOOT
  // ────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    HomepageAnimations.init();
  });

  // Expose for external use if needed
  window.HomepageAnimations = HomepageAnimations;

})();
