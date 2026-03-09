/* ═══════════════════════════════════════════════════════════════
   E-MENUM ENTERPRISE HERO — JS
   Single immersive hero with GSAP word-by-word reveal,
   floating elements, and QR code generation.
   ═══════════════════════════════════════════════════════════════ */

// ════════ QR SCAN SVG (static showcase) ════════
var HERO_QR_SVG = '<svg width="320" height="210" viewBox="0 0 320 210" class="svg-qr" style="overflow:visible">' +
  '<defs>' +
  '<linearGradient id="qrBeam" x1="0" y1="0" x2="0" y2="1">' +
  '<stop offset="0%" stop-color="transparent"/>' +
  '<stop offset="50%" stop-color="#22c55e" stop-opacity=".9"/>' +
  '<stop offset="100%" stop-color="transparent"/>' +
  '</linearGradient>' +
  '<clipPath id="qr-clip"><rect x="90" y="30" width="90" height="90" rx="8"/></clipPath>' +
  '</defs>' +
  '<rect x="82" y="22" width="106" height="106" rx="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.25)" stroke-width="1.5"/>' +
  '<g opacity=".6">' +
  '<rect x="96" y="36" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>' +
  '<rect x="120" y="36" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>' +
  '<rect x="132" y="36" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>' +
  '<rect x="152" y="36" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>' +
  '<rect x="96" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>' +
  '<rect x="108" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.4)"/>' +
  '<rect x="120" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.25)"/>' +
  '<rect x="132" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.4)"/>' +
  '<rect x="144" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>' +
  '<rect x="164" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>' +
  '<rect x="96" y="72" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>' +
  '<rect x="120" y="72" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>' +
  '<rect x="132" y="72" width="8" height="8" rx="2" fill="rgba(34,197,94,.4)"/>' +
  '<rect x="120" y="84" width="8" height="8" rx="2" fill="rgba(34,197,94,.25)"/>' +
  '<rect x="132" y="84" width="8" height="8" rx="2" fill="rgba(34,197,94,.35)"/>' +
  '<rect x="152" y="72" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>' +
  '<rect x="133" y="73" width="8" height="8" rx="1" fill="#22c55e"/>' +
  '</g>' +
  '<rect class="qr-beam" x="84" y="24" width="102" height="6" rx="3" fill="url(#qrBeam)" clip-path="url(#qr-clip)"/>' +
  '<path class="qr-corner" d="M90,50 L90,32 L108,32" stroke-width="3"/>' +
  '<path class="qr-corner" d="M174,32 L192,32 L192,50" stroke-width="3"/>' +
  '<path class="qr-corner" d="M90,100 L90,118 L108,118" stroke-width="3"/>' +
  '<rect class="phone-body" x="210" y="15" width="85" height="148" rx="16"/>' +
  '<rect class="phone-screen" x="215" y="20" width="75" height="138" rx="13"/>' +
  '<rect class="menu-line" x="220" y="28" width="65" height="6" rx="3" fill="#22c55e" opacity=".7" style="animation-delay:.2s"/>' +
  '<rect class="menu-line" x="220" y="38" width="45" height="4" rx="2" fill="rgba(34,197,94,.4)" style="animation-delay:.4s"/>' +
  '<rect x="220" y="50" width="30" height="20" rx="6" fill="rgba(34,197,94,.15)"/>' +
  '<rect class="menu-line" x="254" y="54" width="30" height="4" rx="2" fill="rgba(34,197,94,.4)" style="animation-delay:.6s"/>' +
  '<rect class="menu-line" x="254" y="62" width="20" height="3" rx="1.5" fill="rgba(34,197,94,.25)" style="animation-delay:.8s"/>' +
  '<rect x="220" y="78" width="30" height="20" rx="6" fill="rgba(34,197,94,.1)"/>' +
  '<rect class="menu-line" x="254" y="82" width="28" height="4" rx="2" fill="rgba(34,197,94,.35)" style="animation-delay:1s"/>' +
  '<rect class="menu-line" x="254" y="90" width="18" height="3" rx="1.5" fill="rgba(34,197,94,.2)" style="animation-delay:1.2s"/>' +
  '<rect x="236" y="106" width="44" height="20" rx="10" fill="rgba(34,197,94,.15)" stroke="rgba(34,197,94,.3)" stroke-width="1"/>' +
  '<text x="258" y="120" text-anchor="middle" font-size="9" fill="#4ade80" font-weight="700">₺185</text>' +
  '<circle class="success-ring" cx="135" cy="175" r="26"/>' +
  '<path class="check-mark" d="M123,175 L131,183 L148,165"/>' +
  '<path d="M195,80 Q202,80 210,80" stroke="rgba(34,197,94,.35)" stroke-width="1.5" stroke-dasharray="3,3" fill="none"/>' +
  '</svg>';


// ════════ SPLIT TEXT UTILITY ════════
function heroSplitWords(el) {
  if (!el || el.dataset.heroSplit === 'done') return [];
  var text = el.textContent.trim();
  if (!text) return [];
  var words = text.split(/\s+/);
  // Preserve the gradient class if present
  var isGrad = el.classList.contains('hero-grad');
  el.innerHTML = words.map(function(w) {
    return '<span class="hero-word-wrap"><span class="hero-word">' + w + '</span></span>';
  }).join(' ');
  el.dataset.heroSplit = 'done';
  // If gradient, apply to each word span
  if (isGrad) {
    el.querySelectorAll('.hero-word').forEach(function(w) {
      w.classList.add('hero-grad-word');
    });
  }
  return el.querySelectorAll('.hero-word');
}

// ════════ QR CODE GENERATOR (independent of GSAP) ════════
function heroGenerateQR(container) {
  var qrBox = container.querySelector('.hero-qr-box');
  if (!qrBox || qrBox.children.length > 0) return;
  if (typeof QRCode !== 'undefined') {
    new QRCode(qrBox, {
      text: 'https://e-menum.net/demo',
      width: 100, height: 100,
      colorDark: '#0a1a0f', colorLight: '#ffffff',
      correctLevel: QRCode.CorrectLevel.M
    });
  } else {
    // QRCode library not yet loaded — retry once
    setTimeout(function() {
      if (typeof QRCode !== 'undefined' && qrBox.children.length === 0) {
        new QRCode(qrBox, {
          text: 'https://e-menum.net/demo',
          width: 100, height: 100,
          colorDark: '#0a1a0f', colorLight: '#ffffff',
          correctLevel: QRCode.CorrectLevel.M
        });
      }
    }, 500);
  }
}

// ════════ ENTERPRISE HERO INIT ════════
function initHeroEnterprise(containerId) {
  var container = document.getElementById(containerId);
  if (!container) return;

  // Inject QR scan SVG + generate QR code (no GSAP dependency)
  var animArea = container.querySelector('#hero-main-anim');
  if (animArea) {
    animArea.innerHTML = HERO_QR_SVG;
  }
  heroGenerateQR(container);

  // GSAP animations — graceful skip if library not loaded
  if (typeof gsap === 'undefined') return;

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion) {
    // Show everything immediately
    container.querySelectorAll('[data-hero-enter], [data-hero-float]').forEach(function(el) {
      el.style.opacity = '1';
    });
    return;
  }

  // ─── Gather elements ───
  var orbs = container.querySelectorAll('.hero-orb');
  var enterEls = container.querySelectorAll('[data-hero-enter]');
  var floatEls = container.querySelectorAll('[data-hero-float]');
  var wordTargets = container.querySelectorAll('[data-hero-words]');

  // ─── Set initial states ───
  gsap.set(enterEls, { opacity: 0, y: 28 });
  gsap.set(floatEls, { opacity: 0, scale: 0.85, transformOrigin: 'center' });
  gsap.set(orbs, { opacity: 0 });

  // ─── Split headline words ───
  var allWords = [];
  wordTargets.forEach(function(el) {
    // First make parent visible for splitting
    el.style.opacity = '1';
    var words = heroSplitWords(el);
    words.forEach(function(w) { allWords.push(w); });
  });
  if (allWords.length) {
    gsap.set(allWords, { opacity: 0, y: 35 });
  }

  // ─── Master timeline ───
  var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

  // 1. Orbs fade in
  orbs.forEach(function(o, i) {
    tl.to(o, { opacity: 1, duration: 1.5 }, i * 0.3);
  });

  // 2. Badge enters
  var badge = container.querySelector('.hero-badge');
  if (badge) {
    tl.to(badge, { opacity: 1, y: 0, duration: 0.6 }, 0.2);
  }

  // 3. Words reveal (word-by-word stagger)
  if (allWords.length) {
    tl.to(allWords, {
      opacity: 1, y: 0,
      duration: 0.5, stagger: 0.06,
      ease: 'power3.out'
    }, 0.4);
  }

  // 4. Subtitle, pain points, CTA, micro, trust (after headline)
  var contentEls = [
    container.querySelector('.hero-sub'),
    container.querySelector('.hero-pains'),
    container.querySelector('.hero-cta-row'),
    container.querySelector('.hero-micro'),
    container.querySelector('.hero-trust-row')
  ].filter(Boolean);

  contentEls.forEach(function(el, i) {
    tl.to(el, { opacity: 1, y: 0, duration: 0.6 }, 0.8 + i * 0.12);
  });

  // 5. Showcase card + floats
  var showcase = container.querySelector('.hero-showcase');
  if (showcase) {
    tl.to(showcase, { opacity: 1, y: 0, duration: 0.8 }, 0.6);
  }

  floatEls.forEach(function(el, i) {
    tl.to(el, { opacity: 1, scale: 1, duration: 0.7 }, 1.0 + i * 0.15);
  });

  // 6. City bar
  var cityBar = container.querySelector('.hero-city-bar');
  if (cityBar && cityBar.closest('[data-hero-enter]')) {
    tl.to(cityBar.closest('[data-hero-enter]'), { opacity: 1, y: 0, duration: 0.6 }, 1.3);
  }

  // ─── Subtle float animations (infinite) ───
  if (showcase) gsap.to(showcase, { y: -8, duration: 3.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 2 });
  var sf = container.querySelector('.hero-stats-float');
  var qrf = container.querySelector('.hero-qr-float');
  if (sf) gsap.to(sf, { y: 6, duration: 4, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 2.5 });
  if (qrf) gsap.to(qrf, { y: -6, duration: 3.8, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 3 });
}

// ════════ SIMPLE HERO (other pages — no showcase) ════════
function initHeroSimple(containerId) {
  var container = document.getElementById(containerId);
  if (!container || typeof gsap === 'undefined') return;

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion) {
    container.querySelectorAll('[data-hero-enter]').forEach(function(el) {
      el.style.opacity = '1';
    });
    return;
  }

  var orbs = container.querySelectorAll('.hero-orb');
  var enterEls = container.querySelectorAll('[data-hero-enter]');

  gsap.set(enterEls, { opacity: 0, y: 28 });
  gsap.set(orbs, { opacity: 0 });

  var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  orbs.forEach(function(o, i) { tl.to(o, { opacity: 1, duration: 1.5 }, i * 0.3); });
  enterEls.forEach(function(el, i) {
    tl.to(el, { opacity: 1, y: 0, duration: 0.7 }, 0.25 + i * 0.1);
  });
}
