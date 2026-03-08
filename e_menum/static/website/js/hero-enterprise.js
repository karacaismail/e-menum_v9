/* ═══════════════════════════════════════════════════════════════
   E-MENUM ENTERPRISE HERO — JS
   Slide carousel, GSAP entrance, QR code generation
   ═══════════════════════════════════════════════════════════════ */

// ════════ SVG ANIMATIONS ════════
const HERO_ANIMS = {
qr: `
<svg width="320" height="210" viewBox="0 0 320 210" class="svg-qr" style="overflow:visible">
  <defs>
    <linearGradient id="qrBeam" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="transparent"/>
      <stop offset="50%" stop-color="#22c55e" stop-opacity=".9"/>
      <stop offset="100%" stop-color="transparent"/>
    </linearGradient>
    <clipPath id="qr-clip"><rect x="90" y="30" width="90" height="90" rx="8"/></clipPath>
  </defs>
  <rect x="82" y="22" width="106" height="106" rx="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.25)" stroke-width="1.5"/>
  <g opacity=".6">
    <rect x="96" y="36" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>
    <rect x="120" y="36" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>
    <rect x="132" y="36" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>
    <rect x="152" y="36" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>
    <rect x="96" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>
    <rect x="108" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.4)"/>
    <rect x="120" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.25)"/>
    <rect x="132" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.4)"/>
    <rect x="144" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>
    <rect x="164" y="60" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>
    <rect x="96" y="72" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>
    <rect x="120" y="72" width="8" height="8" rx="2" fill="rgba(34,197,94,.3)"/>
    <rect x="132" y="72" width="8" height="8" rx="2" fill="rgba(34,197,94,.4)"/>
    <rect x="120" y="84" width="8" height="8" rx="2" fill="rgba(34,197,94,.25)"/>
    <rect x="132" y="84" width="8" height="8" rx="2" fill="rgba(34,197,94,.35)"/>
    <rect x="152" y="72" width="20" height="20" rx="3" fill="rgba(34,197,94,.5)"/>
    <rect x="133" y="73" width="8" height="8" rx="1" fill="#22c55e"/>
  </g>
  <rect class="qr-beam" x="84" y="24" width="102" height="6" rx="3" fill="url(#qrBeam)" clip-path="url(#qr-clip)"/>
  <path class="qr-corner" d="M90,50 L90,32 L108,32" stroke-width="3"/>
  <path class="qr-corner" d="M174,32 L192,32 L192,50" stroke-width="3"/>
  <path class="qr-corner" d="M90,100 L90,118 L108,118" stroke-width="3"/>
  <rect class="phone-body" x="210" y="15" width="85" height="148" rx="16"/>
  <rect class="phone-screen" x="215" y="20" width="75" height="138" rx="13"/>
  <rect class="menu-line" x="220" y="28" width="65" height="6" rx="3" fill="#22c55e" opacity=".7" style="animation-delay:.2s"/>
  <rect class="menu-line" x="220" y="38" width="45" height="4" rx="2" fill="rgba(34,197,94,.4)" style="animation-delay:.4s"/>
  <rect x="220" y="50" width="30" height="20" rx="6" fill="rgba(34,197,94,.15)"/>
  <rect class="menu-line" x="254" y="54" width="30" height="4" rx="2" fill="rgba(34,197,94,.4)" style="animation-delay:.6s"/>
  <rect class="menu-line" x="254" y="62" width="20" height="3" rx="1.5" fill="rgba(34,197,94,.25)" style="animation-delay:.8s"/>
  <rect x="220" y="78" width="30" height="20" rx="6" fill="rgba(34,197,94,.1)"/>
  <rect class="menu-line" x="254" y="82" width="28" height="4" rx="2" fill="rgba(34,197,94,.35)" style="animation-delay:1s"/>
  <rect class="menu-line" x="254" y="90" width="18" height="3" rx="1.5" fill="rgba(34,197,94,.2)" style="animation-delay:1.2s"/>
  <rect x="236" y="106" width="44" height="20" rx="10" fill="rgba(34,197,94,.15)" stroke="rgba(34,197,94,.3)" stroke-width="1"/>
  <text x="258" y="120" text-anchor="middle" font-size="9" fill="#4ade80" font-weight="700">₺185</text>
  <circle class="success-ring" cx="135" cy="175" r="26"/>
  <path class="check-mark" d="M123,175 L131,183 L148,165"/>
  <path d="M195,80 Q202,80 210,80" stroke="rgba(34,197,94,.35)" stroke-width="1.5" stroke-dasharray="3,3" fill="none"/>
</svg>`,

price: `
<svg width="320" height="210" viewBox="0 0 320 210" class="svg-price" style="overflow:visible">
  <defs>
    <linearGradient id="tagGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="rgba(15,35,18,.98)"/>
      <stop offset="100%" stop-color="rgba(8,21,10,.98)"/>
    </linearGradient>
  </defs>
  <rect class="tag-body" x="85" y="40" width="150" height="90" rx="16" fill="url(#tagGrad)" stroke="rgba(34,197,94,.3)" stroke-width="1.5"/>
  <circle cx="105" cy="60" r="6" fill="none" stroke="rgba(34,197,94,.5)" stroke-width="1.5"/>
  <g class="price-old">
    <text x="160" y="80" text-anchor="middle" font-size="22" fill="rgba(200,200,200,.5)" font-family="Fraunces,serif" font-weight="900">₺145</text>
    <line x1="128" y1="78" x2="192" y2="78" stroke="rgba(255,100,100,.6)" stroke-width="2"/>
  </g>
  <g class="price-new" style="transform:scale(.8);transform-origin:160px 110px">
    <text x="160" y="118" text-anchor="middle" font-size="26" fill="#4ade80" font-family="Fraunces,serif" font-weight="900">₺185</text>
  </g>
  <rect x="100" y="125" width="120" height="3" rx="1.5" fill="rgba(34,197,94,.15)"/>
  <rect class="update-bar" x="100" y="125" width="120" height="3" rx="1.5" fill="#22c55e"/>
  <g class="edit-icon" style="transform-origin:245px 55px">
    <rect x="232" y="42" width="26" height="26" rx="13" fill="rgba(34,197,94,.12)" stroke="rgba(34,197,94,.3)" stroke-width="1"/>
    <path d="M239,62 L245,54 L251,60 L245,66 Z" fill="none" stroke="#4ade80" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M239,62 L237,65" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round"/>
  </g>
  <circle class="spark" cx="195" cy="50" r="4" fill="#fbbf24" style="--d:.9s"/>
  <circle class="spark" cx="205" cy="42" r="3" fill="#22c55e" style="--d:1.1s"/>
  <circle class="spark" cx="188" cy="44" r="3.5" fill="#4ade80" style="--d:1.3s"/>
  <circle class="spark" cx="200" cy="35" r="2.5" fill="#fbbf24" style="--d:1s"/>
  <g style="transform:translate(0,10)">
    <rect x="70" y="155" width="55" height="30" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.2)" stroke-width="1"/>
    <rect x="76" y="161" width="30" height="4" rx="2" fill="rgba(34,197,94,.4)"/>
    <rect x="76" y="169" width="20" height="3" rx="1.5" fill="rgba(34,197,94,.2)"/>
    <rect x="133" y="155" width="55" height="30" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.2)" stroke-width="1"/>
    <rect x="139" y="161" width="30" height="4" rx="2" fill="rgba(34,197,94,.4)"/>
    <rect x="139" y="169" width="20" height="3" rx="1.5" fill="rgba(34,197,94,.2)"/>
    <rect x="196" y="155" width="55" height="30" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.35)" stroke-width="1"/>
    <rect x="202" y="161" width="30" height="4" rx="2" fill="#22c55e" opacity=".7"/>
    <rect x="202" y="169" width="22" height="3" rx="1.5" fill="rgba(34,197,94,.3)"/>
    <circle cx="239" cy="153" r="6" fill="#22c55e"/>
    <path d="M236,153 L238,155.5 L242,150.5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </g>
</svg>`,

order: `
<svg width="320" height="210" viewBox="0 0 320 210" class="svg-order" style="overflow:visible">
  <circle class="ring-wave" cx="160" cy="75" r="28"/>
  <circle class="ring-wave" cx="160" cy="75" r="28" style="animation-delay:.5s"/>
  <circle class="ring-wave" cx="160" cy="75" r="28" style="animation-delay:1s"/>
  <g class="bell-icon">
    <path d="M150,82 Q150,62 160,62 Q170,62 170,82 L173,85 H147 Z" fill="rgba(34,197,94,.2)" stroke="#22c55e" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M157,86 Q157,90 160,90 Q163,90 163,86" fill="none" stroke="#22c55e" stroke-width="1.5"/>
    <circle class="notif-dot" cx="171" cy="63" r="5" fill="#ef4444"/>
    <text x="171" y="67" text-anchor="middle" font-size="7" fill="#fff" font-weight="700">3</text>
  </g>
  <g class="ticket-body" style="--d:.3s">
    <rect x="50" y="110" width="90" height="55" rx="10" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.25)" stroke-width="1.2"/>
    <line x1="50" y1="128" x2="140" y2="128" stroke="rgba(34,197,94,.15)" stroke-width="1" stroke-dasharray="3,3"/>
    <text x="95" y="124" text-anchor="middle" font-size="8" fill="#4ade80" font-weight="700">#1842</text>
    <rect x="58" y="133" width="50" height="3.5" rx="1.5" fill="rgba(34,197,94,.3)"/>
    <rect x="58" y="141" width="35" height="3" rx="1.5" fill="rgba(34,197,94,.2)"/>
    <rect x="58" y="149" width="40" height="3" rx="1.5" fill="rgba(34,197,94,.18)"/>
  </g>
  <g class="ticket-body" style="--d:.7s">
    <rect x="180" y="110" width="90" height="55" rx="10" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.25)" stroke-width="1.2"/>
    <line x1="180" y1="128" x2="270" y2="128" stroke="rgba(34,197,94,.15)" stroke-width="1" stroke-dasharray="3,3"/>
    <text x="225" y="124" text-anchor="middle" font-size="8" fill="#4ade80" font-weight="700">#1843</text>
    <rect x="188" y="133" width="50" height="3.5" rx="1.5" fill="rgba(34,197,94,.3)"/>
    <rect x="188" y="141" width="35" height="3" rx="1.5" fill="rgba(34,197,94,.2)"/>
    <rect x="188" y="149" width="40" height="3" rx="1.5" fill="rgba(34,197,94,.18)"/>
  </g>
  <circle cx="130" cy="111" r="11" fill="rgba(34,197,94,.15)" stroke="rgba(34,197,94,.4)" stroke-width="1.2"/>
  <path class="check-anim" d="M124,111 L128,115 L137,106" style="--d2:.8s"/>
  <circle cx="260" cy="111" r="11" fill="rgba(34,197,94,.15)" stroke="rgba(34,197,94,.4)" stroke-width="1.2"/>
  <path class="check-anim" d="M254,111 L258,115 L267,106" style="--d2:1.2s"/>
  <path d="M145,137 L175,137" stroke="rgba(34,197,94,.3)" stroke-width="1.5" stroke-dasharray="4,3" fill="none" marker-end="url(#arr)"/>
  <defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 Z" fill="rgba(34,197,94,.5)"/></marker></defs>
  <rect x="128" y="170" width="64" height="22" rx="11" fill="rgba(34,197,94,.1)" stroke="rgba(34,197,94,.25)" stroke-width="1"/>
  <text x="160" y="185" text-anchor="middle" font-size="9" fill="#4ade80" font-weight="600">⏱ 2:14 dk</text>
</svg>`,

campaign: `
<svg width="320" height="210" viewBox="0 0 320 210" class="svg-camp" style="overflow:visible">
  <defs><linearGradient id="starGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#fbbf24"/><stop offset="100%" stop-color="#f59e0b"/></linearGradient></defs>
  <rect class="confetti" x="80" y="0" width="8" height="8" rx="2" fill="#fbbf24" style="--d:0s"/>
  <circle class="confetti" cx="220" cy="0" r="4" fill="#22c55e" style="--d:.3s"/>
  <rect class="confetti" x="150" y="0" width="6" height="6" rx="1" fill="#4ade80" style="--d:.6s"/>
  <circle class="confetti" cx="100" cy="0" r="3" fill="#fbbf24" style="--d:.9s"/>
  <rect class="confetti" x="240" y="0" width="7" height="7" rx="2" fill="#22c55e" style="--d:.4s"/>
  <circle class="confetti" cx="185" cy="0" r="3.5" fill="#fbbf24" style="--d:.15s"/>
  <line class="burst-line" x1="160" y1="105" x2="160" y2="72" style="--d:.9s"/>
  <line class="burst-line" x1="160" y1="105" x2="188" y2="80" style="--d:1s"/>
  <line class="burst-line" x1="160" y1="105" x2="132" y2="80" style="--d:1.1s"/>
  <line class="burst-line" x1="160" y1="105" x2="195" y2="105" style="--d:1.2s"/>
  <line class="burst-line" x1="160" y1="105" x2="125" y2="105" style="--d:1s"/>
  <line class="burst-line" x1="160" y1="105" x2="185" y2="128" style="--d:.95s"/>
  <line class="burst-line" x1="160" y1="105" x2="135" y2="128" style="--d:1.15s"/>
  <circle class="badge-ring" cx="160" cy="105" r="44"/>
  <path class="star-body" d="M160,68 L167,87 H188 L173,99 L179,118 L160,107 L141,118 L147,99 L132,87 H153 Z" fill="url(#starGrad)" stroke="rgba(245,158,11,.4)" stroke-width="1"/>
  <circle cx="160" cy="105" r="22" fill="rgba(8,21,10,.9)" stroke="rgba(245,158,11,.3)" stroke-width="1.5"/>
  <text class="percent-num" x="160" y="112" text-anchor="middle" font-size="20" fill="#fbbf24" font-family="Fraunces,serif" font-weight="900">%20</text>
  <g>
    <rect x="55" y="160" width="80" height="32" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(245,158,11,.25)" stroke-width="1"/>
    <text x="95" y="171" text-anchor="middle" font-size="7" fill="#fbbf24" font-weight="700">ÖĞLE MENÜSÜ</text>
    <text x="95" y="183" text-anchor="middle" font-size="10" fill="#4ade80" font-weight="800">₺85</text>
  </g>
  <g>
    <rect x="145" y="160" width="80" height="32" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.25)" stroke-width="1"/>
    <text x="185" y="171" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">HAPPY HOUR</text>
    <text x="185" y="183" text-anchor="middle" font-size="10" fill="#4ade80" font-weight="800">16-18</text>
  </g>
  <g>
    <rect x="235" y="160" width="55" height="32" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.2)" stroke-width="1"/>
    <text x="262" y="176" text-anchor="middle" font-size="8" fill="#4ade80">+1 Daha</text>
  </g>
</svg>`,

analytics: `
<svg width="320" height="210" viewBox="0 0 320 210" class="svg-analytics" style="overflow:visible">
  <defs>
    <linearGradient id="trendGrad" x1="0" y1="1" x2="1" y2="0"><stop offset="0%" stop-color="#22c55e"/><stop offset="100%" stop-color="#4ade80"/></linearGradient>
    <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#4ade80"/><stop offset="100%" stop-color="#16a34a"/></linearGradient>
  </defs>
  <rect x="55" y="20" width="210" height="140" rx="16" fill="rgba(10,25,13,.95)" stroke="rgba(34,197,94,.15)" stroke-width="1.2"/>
  <line class="grid-line" x1="55" y1="110" x2="265" y2="110"/>
  <line class="grid-line" x1="55" y1="90" x2="265" y2="90"/>
  <line class="grid-line" x1="55" y1="70" x2="265" y2="70"/>
  <line class="grid-line" x1="55" y1="50" x2="265" y2="50"/>
  <rect class="bar-fill" x="78" y="78" width="16" height="32" rx="4" fill="url(#barGrad)" opacity=".7" style="--d:.15s"/>
  <rect class="bar-fill" x="102" y="68" width="16" height="42" rx="4" fill="url(#barGrad)" opacity=".75" style="--d:.3s"/>
  <rect class="bar-fill" x="126" y="85" width="16" height="25" rx="4" fill="url(#barGrad)" opacity=".65" style="--d:.45s"/>
  <rect class="bar-fill" x="150" y="58" width="16" height="52" rx="4" fill="url(#barGrad)" style="--d:.6s"/>
  <rect class="bar-fill" x="174" y="48" width="16" height="62" rx="4" fill="url(#barGrad)" style="--d:.75s"/>
  <rect class="bar-fill" x="198" y="38" width="16" height="72" rx="4" fill="url(#barGrad)" style="--d:.9s"/>
  <rect class="bar-fill" x="222" y="30" width="16" height="80" rx="4" fill="url(#barGrad)" style="--d:1.05s"/>
  <path class="trend-line" d="M86,110 L110,100 L134,108 L158,82 L182,72 L206,55 L230,42"/>
  <circle class="dot-pulse" cx="86" cy="110" r="4" fill="#22c55e" style="--d:1.5s"/>
  <circle class="dot-pulse" cx="182" cy="72" r="4" fill="#22c55e" style="--d:1.7s"/>
  <circle cx="230" cy="42" r="5" fill="#4ade80"/>
  <g class="up-arrow" style="transform:translateY(0)">
    <rect x="220" y="28" width="40" height="18" rx="9" fill="rgba(34,197,94,.15)" stroke="rgba(34,197,94,.35)" stroke-width="1"/>
    <text x="240" y="40" text-anchor="middle" font-size="9" fill="#4ade80" font-weight="700">+34%</text>
  </g>
  <rect x="62" y="170" width="56" height="26" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.2)" stroke-width="1"/>
  <text x="90" y="181" text-anchor="middle" font-size="7" fill="#4ade80">QR Tarama</text>
  <text x="90" y="191" text-anchor="middle" font-size="10" fill="#86efac" font-weight="800">1,247</text>
  <rect x="126" y="170" width="68" height="26" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.2)" stroke-width="1"/>
  <text x="160" y="181" text-anchor="middle" font-size="7" fill="#4ade80">Avg. Süre</text>
  <text x="160" y="191" text-anchor="middle" font-size="10" fill="#86efac" font-weight="800">4.2 dk</text>
  <rect x="202" y="170" width="56" height="26" rx="8" fill="rgba(15,35,18,.9)" stroke="rgba(34,197,94,.3)" stroke-width="1"/>
  <text x="230" y="181" text-anchor="middle" font-size="7" fill="#4ade80">Sipariş</text>
  <text x="230" y="191" text-anchor="middle" font-size="10" fill="#4ade80" font-weight="800">89</text>
</svg>`,

branches: `
<svg width="320" height="210" viewBox="0 0 320 210" class="svg-branches" style="overflow:visible">
  <circle class="hub-pulse" cx="160" cy="105" r="22"/>
  <circle cx="160" cy="105" r="16" fill="rgba(34,197,94,.15)" stroke="rgba(34,197,94,.4)" stroke-width="1.5"/>
  <text x="160" y="110" text-anchor="middle" font-size="9" fill="#4ade80" font-weight="700">MERKEZ</text>
  <path class="conn-line" d="M148,97 L105,65" style="--d:.8s"/>
  <path class="conn-line" d="M172,97 L215,65" style="--d:1s"/>
  <path class="conn-line" d="M144,105 L88,105" style="--d:1.2s"/>
  <path class="conn-line" d="M176,105 L232,105" style="--d:1.4s"/>
  <path class="conn-line" d="M148,113 L100,148" style="--d:1.6s"/>
  <path class="conn-line" d="M172,113 L220,148" style="--d:1.8s"/>
  <g class="pin" style="--d:.2s">
    <circle cx="99" cy="58" r="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.3)" stroke-width="1.2"/>
    <text x="99" y="56" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">IST</text>
    <text x="99" y="66" text-anchor="middle" font-size="7" fill="#86efac">450+</text>
  </g>
  <g class="pin" style="--d:.4s">
    <circle cx="221" cy="58" r="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.3)" stroke-width="1.2"/>
    <text x="221" y="56" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">ANK</text>
    <text x="221" y="66" text-anchor="middle" font-size="7" fill="#86efac">120+</text>
  </g>
  <g class="pin" style="--d:.6s">
    <circle cx="77" cy="105" r="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.3)" stroke-width="1.2"/>
    <text x="77" y="103" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">IZM</text>
    <text x="77" y="113" text-anchor="middle" font-size="7" fill="#86efac">95+</text>
  </g>
  <g class="pin" style="--d:.8s">
    <circle cx="243" cy="105" r="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.3)" stroke-width="1.2"/>
    <text x="243" y="103" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">ANT</text>
    <text x="243" y="113" text-anchor="middle" font-size="7" fill="#86efac">80+</text>
  </g>
  <g class="pin" style="--d:1s">
    <circle cx="99" cy="152" r="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.3)" stroke-width="1.2"/>
    <text x="99" y="150" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">GAZ</text>
    <text x="99" y="160" text-anchor="middle" font-size="7" fill="#86efac">40+</text>
  </g>
  <g class="pin" style="--d:1.2s">
    <circle cx="221" cy="152" r="14" fill="rgba(15,35,18,.95)" stroke="rgba(34,197,94,.3)" stroke-width="1.2"/>
    <text x="221" y="150" text-anchor="middle" font-size="7" fill="#4ade80" font-weight="700">KON</text>
    <text x="221" y="160" text-anchor="middle" font-size="7" fill="#86efac">35+</text>
  </g>
  <g class="pin-count" style="--d:1.5s">
    <rect x="125" y="170" width="70" height="24" rx="12" fill="rgba(34,197,94,.1)" stroke="rgba(34,197,94,.3)" stroke-width="1"/>
    <text x="160" y="186" text-anchor="middle" font-size="9" fill="#4ade80" font-weight="700">1,200+ Şube</text>
  </g>
</svg>`
};

// ════════ HERO SLIDESHOW ENGINE ════════
function initHeroSlideshow(slidesData, containerId) {
  const container = document.getElementById(containerId);
  if (!container || typeof gsap === 'undefined') return;

  let current = 0;
  let timer = null;
  let fillTween = null;
  const DURATION = 5000;
  const SLIDES = slidesData;

  // Generate QR code if element exists
  const qrBox = container.querySelector('.hero-qr-box');
  if (qrBox && typeof QRCode !== 'undefined') {
    new QRCode(qrBox, {
      text: 'https://e-menum.net/demo',
      width: 100, height: 100,
      colorDark: '#0a1a0f', colorLight: '#ffffff',
      correctLevel: QRCode.CorrectLevel.M
    });
  }

  function renderSlide(idx, dir) {
    const s = SLIDES[idx];
    const animArea = container.querySelector('.hero-slide-anim');
    const content = container.querySelector('.hero-slide-content');
    const h1s = container.querySelector('.hero-h1-static');
    const h1d = container.querySelector('.hero-h1-dyn');
    const sub = container.querySelector('.hero-sub');
    const pains = container.querySelectorAll('.hero-pain-text');
    const badgeTxt = container.querySelector('.hero-badge-txt');
    const slLabel = container.querySelector('.hero-sl-label');
    const slTitle = container.querySelector('.hero-sl-title');
    const slDesc = container.querySelector('.hero-sl-desc');
    const stats = container.querySelectorAll('.hero-st');
    const statLbls = container.querySelectorAll('.hero-stat-lbl');

    // Update nav
    container.querySelectorAll('.hero-sn-item').forEach((el, i) => {
      el.classList.toggle('active', i === idx);
    });

    // Elements to animate
    const animEls = [animArea, content, h1s, h1d, sub];
    pains.forEach(p => animEls.push(p));
    if (badgeTxt) animEls.push(badgeTxt);

    gsap.to(animEls, {
      opacity: 0, x: dir === 1 ? -20 : 20, duration: .3, ease: 'power2.in',
      onComplete: () => {
        if (badgeTxt) badgeTxt.textContent = s.badge;
        if (h1s) h1s.textContent = s.h1s;
        if (h1d) {
          h1d.className = 'hero-slide-h1 hero-' + s.gradClass;
          h1d.textContent = s.h1d;
        }
        if (sub) sub.textContent = s.sub;
        pains.forEach((p, i) => { if (s.p[i]) p.textContent = s.p[i]; });
        if (slLabel) slLabel.innerHTML = '<svg width="10" height="10" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="rgba(34,197,94,.3)"/><circle cx="5" cy="5" r="2" fill="#22c55e"/></svg>' + s.label;
        if (slTitle) slTitle.textContent = s.title;
        if (slDesc) slDesc.textContent = s.desc;
        stats.forEach((st, i) => { if (s.stats[i]) st.textContent = s.stats[i].n; });
        statLbls.forEach((lbl, i) => { if (s.stats[i]) lbl.textContent = s.stats[i].l; });
        // Re-render SVG animation
        if (animArea) animArea.innerHTML = HERO_ANIMS[s.anim] || '';
        // Animate in
        gsap.fromTo(animEls,
          { opacity: 0, x: dir === 1 ? 20 : -20 },
          { opacity: 1, x: 0, duration: .4, ease: 'power2.out', stagger: .04 }
        );
      }
    });
  }

  function startProgress(idx) {
    if (fillTween) fillTween.kill();
    container.querySelectorAll('.hero-sn-fill').forEach(el => el.style.width = '0%');
    const fill = container.querySelector('.hero-sn-fill-' + idx);
    if (!fill) return;
    fill.style.transition = 'none';
    fill.style.width = '0%';
    fillTween = gsap.to(fill, { width: '100%', duration: DURATION / 1000, ease: 'none' });
  }

  function goSlide(idx) {
    if (idx === current) return;
    const dir = idx > current ? 1 : -1;
    current = idx;
    if (timer) clearTimeout(timer);
    renderSlide(current, dir);
    startProgress(current);
    scheduleNext();
  }

  function next() {
    current = (current + 1) % SLIDES.length;
    renderSlide(current, 1);
    startProgress(current);
    scheduleNext();
  }

  function scheduleNext() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(next, DURATION);
  }

  // Expose goSlide globally for onclick
  window['heroGoSlide_' + containerId] = goSlide;

  // Pause on hover
  const card = container.querySelector('.hero-slide-card');
  if (card) {
    card.addEventListener('mouseenter', () => {
      if (timer) clearTimeout(timer);
      if (fillTween) fillTween.pause();
    });
    card.addEventListener('mouseleave', () => {
      if (fillTween) fillTween.resume();
      scheduleNext();
    });
  }

  // Init first slide
  const animArea = container.querySelector('.hero-slide-anim');
  if (animArea && SLIDES[0]) {
    animArea.innerHTML = HERO_ANIMS[SLIDES[0].anim] || '';
  }
  startProgress(0);
  scheduleNext();

  // Entrance animation
  const orbs = container.querySelectorAll('.hero-orb');
  const enterEls = container.querySelectorAll('[data-hero-enter]');
  const floatEls = container.querySelectorAll('[data-hero-float]');

  gsap.set(enterEls, { opacity: 0, y: 28 });
  gsap.set(floatEls, { opacity: 0, scale: .85, transformOrigin: 'center' });
  gsap.set(orbs, { opacity: 0 });

  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  orbs.forEach((o, i) => tl.to(o, { opacity: 1, duration: 1.5 }, i * 0.3));

  enterEls.forEach((el, i) => {
    tl.to(el, { opacity: 1, y: 0, duration: 0.7 }, 0.25 + i * 0.1);
  });

  floatEls.forEach((el, i) => {
    tl.to(el, { opacity: 1, scale: 1, duration: 0.7 }, 1.0 + i * 0.1);
  });

  // Subtle float animations
  const showcase = container.querySelector('.hero-showcase');
  const sf = container.querySelector('.hero-stats-float');
  const qrf = container.querySelector('.hero-qr-float');
  if (showcase) gsap.to(showcase, { y: -8, duration: 3.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: .5 });
  if (sf) gsap.to(sf, { y: 6, duration: 4, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1 });
  if (qrf) gsap.to(qrf, { y: -6, duration: 3.8, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1.5 });
}

// ════════ SIMPLE HERO (no slideshow) ════════
function initHeroSimple(containerId) {
  const container = document.getElementById(containerId);
  if (!container || typeof gsap === 'undefined') return;

  const orbs = container.querySelectorAll('.hero-orb');
  const enterEls = container.querySelectorAll('[data-hero-enter]');

  gsap.set(enterEls, { opacity: 0, y: 28 });
  gsap.set(orbs, { opacity: 0 });

  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  orbs.forEach((o, i) => tl.to(o, { opacity: 1, duration: 1.5 }, i * 0.3));
  enterEls.forEach((el, i) => {
    tl.to(el, { opacity: 1, y: 0, duration: 0.7 }, 0.25 + i * 0.1);
  });
}
