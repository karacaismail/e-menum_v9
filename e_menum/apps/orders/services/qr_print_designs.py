"""
Brand-aware QR code print design service.

Generates print-ready PDFs using five pre-designed templates that
incorporate the restaurant's Theme colors, logo, and font choices.

Templates:
    ELEGANT  - Clean white background, thin borders, serif-style heading
    MODERN   - Gradient header bar, rounded QR, sans-serif, minimal
    RUSTIC   - Kraft/brown tones, textured feel, warm palette
    VIBRANT  - Bold brand colors, colored QR frame, prominent logo
    MINIMAL  - Ultra-clean, just QR + small text, maximum whitespace

Usage:
    from apps.orders.services.qr_print_designs import QRPrintDesignService

    # Generate branded A4 print PDF
    pdf_buf = QRPrintDesignService.generate_branded_print(
        data_url="https://e-menum.net/q/ABC123/",
        design_template='MODERN',
        design_size='A4',
        org_name='Cafe Istanbul',
        org_logo_url='https://example.com/logo.png',
        theme_colors={'primary': '#3B82F6', 'secondary': '#10B981', ...},
        table_name='Masa 5',
        custom_text='Menumuzu kesfet!',
    )

    # Generate a small table-top card
    card_buf = QRPrintDesignService.generate_table_card(
        data_url="https://e-menum.net/q/ABC123/",
        table_name='Masa 5',
        org_name='Cafe Istanbul',
        theme_colors=theme_dict,
        design_template='ELEGANT',
    )

    # Extract theme colors from an organization's default theme
    colors = QRPrintDesignService.get_theme_colors_from_org(org_instance)
"""

import io
import logging


from apps.orders.services.qr_generator import QRGeneratorService, PRINT_SIZES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default color palettes per template (used when no theme_colors provided)
# ---------------------------------------------------------------------------

_TEMPLATE_DEFAULTS = {
    "ELEGANT": {
        "primary": "#1F2937",
        "secondary": "#6B7280",
        "background": "#FFFFFF",
        "text": "#1F2937",
        "accent": "#D4AF37",
    },
    "MODERN": {
        "primary": "#3B82F6",
        "secondary": "#10B981",
        "background": "#F9FAFB",
        "text": "#111827",
        "accent": "#6366F1",
    },
    "RUSTIC": {
        "primary": "#92400E",
        "secondary": "#B45309",
        "background": "#FDF6EC",
        "text": "#451A03",
        "accent": "#D97706",
    },
    "VIBRANT": {
        "primary": "#DC2626",
        "secondary": "#F59E0B",
        "background": "#FFFFFF",
        "text": "#111827",
        "accent": "#7C3AED",
    },
    "MINIMAL": {
        "primary": "#374151",
        "secondary": "#9CA3AF",
        "background": "#FFFFFF",
        "text": "#374151",
        "accent": "#6B7280",
    },
}

TEMPLATE_CHOICES = list(_TEMPLATE_DEFAULTS.keys())

TEMPLATE_INFO = {
    "ELEGANT": {
        "name": "Elegant",
        "name_tr": "Zarif",
        "description": "Beyaz zemin, ince cizgiler, serif baslk, ust logolu.",
        "icon": "ph-crown",
    },
    "MODERN": {
        "name": "Modern",
        "name_tr": "Modern",
        "description": "Degrade baslik, yuvarlak QR, sans-serif, minimal.",
        "icon": "ph-lightning",
    },
    "RUSTIC": {
        "name": "Rustic",
        "name_tr": "Rustik",
        "description": "Kahverengi tonlar, sicak palet, dokulu his.",
        "icon": "ph-tree",
    },
    "VIBRANT": {
        "name": "Vibrant",
        "name_tr": "Canli",
        "description": "Cesur renkler, renkli QR cerceve, belirgin logo.",
        "icon": "ph-palette",
    },
    "MINIMAL": {
        "name": "Minimal",
        "name_tr": "Minimal",
        "description": "Sadece QR + kucuk yazi, maksimum bosluk.",
        "icon": "ph-minus-circle",
    },
}


def _hex_to_rgb(hex_color):
    """Convert '#RRGGBB' to (r, g, b) tuple."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _darken(hex_color, factor=0.7):
    """Darken a hex color by *factor* (0 = black, 1 = unchanged)."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02X}{g:02X}{b:02X}"


def _lighten(hex_color, factor=0.3):
    """Lighten a hex color toward white by *factor* (0 = unchanged, 1 = white)."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02X}{g:02X}{b:02X}"


class QRPrintDesignService:
    """Generate brand-aware, template-based print PDFs for QR codes."""

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @classmethod
    def generate_branded_print(
        cls,
        data_url,
        design_template="ELEGANT",
        design_size="A4",
        org_name="",
        org_logo_url=None,
        theme_colors=None,
        table_name=None,
        custom_text=None,
    ):
        """
        Generate a print-ready PDF with a brand-aware design template.

        Args:
            data_url: URL to encode in the QR code.
            design_template: One of ELEGANT, MODERN, RUSTIC, VIBRANT, MINIMAL.
            design_size: Paper size key ('10x20cm', 'A5', 'A4', '15x30cm', '20x40cm').
            org_name: Restaurant / organization name.
            org_logo_url: HTTP(S) URL or local path to the organization logo.
            theme_colors: dict with keys 'primary', 'secondary', 'background',
                          'text', 'accent'.  Missing keys filled from template defaults.
            table_name: Optional table identifier (e.g. "Masa 5").
            custom_text: Optional instructional text. Defaults to
                         "Menuyu goruntulemek icin QR kodu tarayin".

        Returns:
            io.BytesIO: PDF buffer, seek(0)'d and ready to read.
        """
        design_template = design_template.upper()
        if design_template not in TEMPLATE_CHOICES:
            design_template = "ELEGANT"

        colors = cls._resolve_colors(design_template, theme_colors)

        renderer = _TEMPLATE_RENDERERS.get(design_template, _render_elegant)
        return renderer(
            data_url=data_url,
            design_size=design_size,
            org_name=org_name,
            org_logo_url=org_logo_url,
            colors=colors,
            table_name=table_name,
            custom_text=custom_text,
        )

    @classmethod
    def generate_table_card(
        cls,
        data_url,
        table_name,
        org_name="",
        org_logo_url=None,
        theme_colors=None,
        design_template="ELEGANT",
    ):
        """
        Generate a small table card (10x20 cm) for table-top QR stands.

        This is a convenience wrapper around generate_branded_print with
        design_size fixed to '10x20cm' and a table-focused custom text.
        """
        return cls.generate_branded_print(
            data_url=data_url,
            design_template=design_template,
            design_size="10x20cm",
            org_name=org_name,
            org_logo_url=org_logo_url,
            theme_colors=theme_colors,
            table_name=table_name,
            custom_text=None,
        )

    @classmethod
    def get_theme_colors_from_org(cls, organization):
        """
        Extract theme colors from the organization's default Theme.

        Returns a dict with keys: primary, secondary, background, text, accent.
        Falls back to template defaults if no default theme is found.
        """
        try:
            from apps.menu.models import Theme

            theme = Theme.objects.filter(
                organization=organization,
                is_default=True,
                is_active=True,
                deleted_at__isnull=True,
            ).first()

            if not theme:
                theme = Theme.objects.filter(
                    organization=organization,
                    is_active=True,
                    deleted_at__isnull=True,
                ).first()

            if theme:
                return {
                    "primary": theme.primary_color or "#3B82F6",
                    "secondary": theme.secondary_color or "#10B981",
                    "background": theme.background_color or "#FFFFFF",
                    "text": theme.text_color or "#1F2937",
                    "accent": theme.accent_color or theme.primary_color or "#3B82F6",
                }
        except Exception as exc:
            logger.warning(
                "Could not load theme colors for org %s: %s", organization, exc
            )

        return _TEMPLATE_DEFAULTS["ELEGANT"].copy()

    @classmethod
    def get_available_templates(cls):
        """
        Return list of available design templates with preview metadata.

        Each item: {'key': 'ELEGANT', 'name': 'Elegant', 'name_tr': '...',
                     'description': '...', 'icon': 'ph-...', 'default_colors': {...}}
        """
        result = []
        for key, info in TEMPLATE_INFO.items():
            result.append(
                {
                    "key": key,
                    **info,
                    "default_colors": _TEMPLATE_DEFAULTS[key].copy(),
                }
            )
        return result

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    @classmethod
    def _resolve_colors(cls, template, theme_colors):
        """Merge user-supplied theme_colors over template defaults."""
        base = _TEMPLATE_DEFAULTS.get(template, _TEMPLATE_DEFAULTS["ELEGANT"]).copy()
        if theme_colors and isinstance(theme_colors, dict):
            for key in ("primary", "secondary", "background", "text", "accent"):
                if theme_colors.get(key):
                    base[key] = theme_colors[key]
        return base


# =========================================================================
# Internal PDF rendering helpers (one function per template)
# =========================================================================


def _get_page_dims(design_size):
    """Return (page_w, page_h) in reportlab points for the given size key."""
    from reportlab.lib.pagesizes import mm

    size_mm = PRINT_SIZES.get(design_size, PRINT_SIZES["A4"])
    return size_mm[0] * mm, size_mm[1] * mm


def _make_qr_pil(data_url, size, logo_url=None):
    """Generate a high-res QR PIL image, optionally overlaying a logo."""
    qr_pil = QRGeneratorService._make_qr_pil(data_url, size=size)
    if logo_url:
        logo_img = QRGeneratorService._load_logo(logo_url)
        if logo_img:
            qr_pil = QRGeneratorService._overlay_logo(qr_pil, logo_img, logo_ratio=0.20)
    return qr_pil


def _pil_to_reader(pil_img):
    """Convert a PIL Image to a reportlab ImageReader."""
    from reportlab.lib.utils import ImageReader

    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _load_logo_pil(logo_url):
    """Load a logo via QRGeneratorService helper; return PIL Image or None."""
    if not logo_url:
        return None
    return QRGeneratorService._load_logo(logo_url)


def _draw_rounded_rect(
    c, x, y, w, h, radius, fill_color=None, stroke_color=None, stroke_width=0.5
):
    """Draw a rounded rectangle on a reportlab canvas."""
    from reportlab.lib.colors import HexColor

    p = c.beginPath()
    r = min(radius, w / 2, h / 2)
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - r, y, x + w, y + r, -90, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - r, y + h - r, x + w, y + h, 0, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - r, x + r, y + h, 90, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + r, y + r, 180, 90)
    p.close()
    if fill_color:
        c.setFillColor(HexColor(fill_color))
    if stroke_color:
        c.setStrokeColor(HexColor(stroke_color))
        c.setLineWidth(stroke_width)
    fill = 1 if fill_color else 0
    stroke = 1 if stroke_color else 0
    c.drawPath(p, fill=fill, stroke=stroke)


def _draw_footer(c, page_w, page_h, color="#9CA3AF", font_size=8):
    """Draw e-menum.net branding at the bottom center."""
    from reportlab.lib.colors import HexColor

    c.setFillColor(HexColor(color))
    c.setFont("Helvetica", font_size)
    c.drawCentredString(page_w / 2, page_h * 0.025, "e-menum.net")


def _default_instruction(table_name):
    """Return the default instruction text, adjusted for table cards."""
    if table_name:
        return "Menuyu goruntulemek icin QR kodu tarayin"
    return "Menuyu goruntulemek icin QR kodu tarayin"


# -------------------------------------------------------------------------
# ELEGANT template
# -------------------------------------------------------------------------


def _render_elegant(
    data_url, design_size, org_name, org_logo_url, colors, table_name, custom_text
):
    """
    ELEGANT: clean white background, thin border, serif-style heading,
    logo at top center.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import mm

    page_w, page_h = _get_page_dims(design_size)
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=(page_w, page_h))

    bg = colors["background"]
    primary = colors["primary"]
    text_col = colors["text"]
    accent = colors["accent"]
    secondary = colors["secondary"]

    # -- Background
    c.setFillColor(HexColor(bg))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # -- Thin border inset
    margin = min(page_w, page_h) * 0.06
    c.setStrokeColor(HexColor(accent))
    c.setLineWidth(0.75)
    c.rect(margin, margin, page_w - 2 * margin, page_h - 2 * margin, fill=0, stroke=1)

    # -- Inner decorative line
    inner_margin = margin + min(page_w, page_h) * 0.015
    c.setStrokeColor(HexColor(_lighten(accent, 0.5)))
    c.setLineWidth(0.25)
    c.rect(
        inner_margin,
        inner_margin,
        page_w - 2 * inner_margin,
        page_h - 2 * inner_margin,
        fill=0,
        stroke=1,
    )

    # -- Logo at top center
    logo_pil = _load_logo_pil(org_logo_url)
    top_y = page_h * 0.85
    if logo_pil:
        logo_display = min(page_w * 0.18, 50 * mm)
        logo_reader = _pil_to_reader(logo_pil)
        logo_x = (page_w - logo_display) / 2
        c.drawImage(
            logo_reader,
            logo_x,
            top_y,
            logo_display,
            logo_display,
            preserveAspectRatio=True,
            anchor="c",
        )
        top_y -= logo_display * 0.15

    # -- Organization name (serif-style)
    if org_name:
        name_y = top_y - page_h * 0.02
        font_size = min(page_w * 0.06, 26)
        c.setFillColor(HexColor(primary))
        c.setFont("Times-Bold", font_size)
        c.drawCentredString(page_w / 2, name_y, org_name)

    # -- Horizontal accent rule
    rule_y = page_h * 0.72
    rule_half = page_w * 0.15
    c.setStrokeColor(HexColor(accent))
    c.setLineWidth(0.5)
    c.line(page_w / 2 - rule_half, rule_y, page_w / 2 + rule_half, rule_y)

    # -- QR code
    qr_display = min(page_w, page_h) * 0.48
    qr_px = max(512, int(qr_display / mm * 3))
    qr_pil = _make_qr_pil(data_url, qr_px, logo_url=org_logo_url)
    qr_reader = _pil_to_reader(qr_pil)

    qr_x = (page_w - qr_display) / 2
    qr_y = page_h * 0.30
    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        qr_display,
        qr_display,
        preserveAspectRatio=True,
        anchor="c",
    )

    # -- Table name
    if table_name:
        table_y = qr_y - page_h * 0.04
        t_size = min(page_w * 0.05, 20)
        c.setFillColor(HexColor(primary))
        c.setFont("Times-Bold", t_size)
        c.drawCentredString(page_w / 2, table_y, table_name)

    # -- Instruction text
    instruction = custom_text or _default_instruction(table_name)
    instr_y = page_h * 0.20 if not table_name else page_h * 0.17
    instr_size = min(page_w * 0.035, 14)
    c.setFillColor(HexColor(secondary))
    c.setFont("Helvetica", instr_size)
    c.drawCentredString(page_w / 2, instr_y, instruction)

    # -- Footer
    _draw_footer(c, page_w, page_h, color=_lighten(text_col, 0.5))

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -------------------------------------------------------------------------
# MODERN template
# -------------------------------------------------------------------------


def _render_modern(
    data_url, design_size, org_name, org_logo_url, colors, table_name, custom_text
):
    """
    MODERN: gradient-colored header bar, rounded QR container,
    sans-serif typography, minimal layout.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import mm

    page_w, page_h = _get_page_dims(design_size)
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=(page_w, page_h))

    bg = colors["background"]
    primary = colors["primary"]
    secondary = colors["secondary"]
    text_col = colors["text"]
    colors["accent"]

    # -- Background
    c.setFillColor(HexColor(bg))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # -- Gradient-style header bar (simulated with two rectangles)
    bar_h = page_h * 0.22
    c.setFillColor(HexColor(primary))
    c.rect(0, page_h - bar_h, page_w, bar_h, fill=1, stroke=0)

    # Lighter secondary strip at the bottom of the bar
    strip_h = bar_h * 0.15
    c.setFillColor(HexColor(secondary))
    c.rect(0, page_h - bar_h, page_w, strip_h, fill=1, stroke=0)

    # -- Logo in header (left-aligned or centered)
    logo_pil = _load_logo_pil(org_logo_url)
    header_center_y = page_h - bar_h / 2

    if logo_pil and org_name:
        # Logo left, name right
        logo_size = min(bar_h * 0.5, 40 * mm)
        logo_reader = _pil_to_reader(logo_pil)
        logo_x = page_w * 0.08
        logo_y = header_center_y - logo_size / 2
        c.drawImage(
            logo_reader,
            logo_x,
            logo_y,
            logo_size,
            logo_size,
            preserveAspectRatio=True,
            anchor="c",
        )

        name_size = min(page_w * 0.055, 24)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", name_size)
        c.drawString(
            logo_x + logo_size + page_w * 0.03,
            header_center_y - name_size * 0.35,
            org_name,
        )
    elif org_name:
        name_size = min(page_w * 0.06, 26)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", name_size)
        c.drawCentredString(page_w / 2, header_center_y - name_size * 0.35, org_name)
    elif logo_pil:
        logo_size = min(bar_h * 0.55, 45 * mm)
        logo_reader = _pil_to_reader(logo_pil)
        c.drawImage(
            logo_reader,
            (page_w - logo_size) / 2,
            header_center_y - logo_size / 2,
            logo_size,
            logo_size,
            preserveAspectRatio=True,
            anchor="c",
        )

    # -- QR in a rounded white card
    card_w = min(page_w * 0.75, page_h * 0.52)
    card_h = card_w * 1.15
    card_x = (page_w - card_w) / 2
    card_y = page_h * 0.18

    _draw_rounded_rect(
        c,
        card_x,
        card_y,
        card_w,
        card_h,
        radius=min(card_w, card_h) * 0.05,
        fill_color="#FFFFFF",
        stroke_color=_lighten(primary, 0.7),
        stroke_width=1,
    )

    # QR inside the card
    qr_display = card_w * 0.75
    qr_px = max(512, int(qr_display / mm * 3))
    qr_pil = _make_qr_pil(data_url, qr_px, logo_url=org_logo_url)
    qr_reader = _pil_to_reader(qr_pil)
    qr_x = card_x + (card_w - qr_display) / 2
    qr_y = card_y + card_h * 0.25
    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        qr_display,
        qr_display,
        preserveAspectRatio=True,
        anchor="c",
    )

    # Table name inside card (below QR)
    if table_name:
        t_y = qr_y - card_h * 0.06
        t_size = min(card_w * 0.08, 18)
        c.setFillColor(HexColor(primary))
        c.setFont("Helvetica-Bold", t_size)
        c.drawCentredString(page_w / 2, t_y, table_name)

    # Instruction inside card top area
    instruction = custom_text or _default_instruction(table_name)
    instr_y = qr_y + qr_display + card_h * 0.04
    instr_size = min(card_w * 0.055, 13)
    c.setFillColor(HexColor(text_col))
    c.setFont("Helvetica", instr_size)
    c.drawCentredString(page_w / 2, instr_y, instruction)

    # -- Footer
    _draw_footer(c, page_w, page_h, color="#9CA3AF")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -------------------------------------------------------------------------
# RUSTIC template
# -------------------------------------------------------------------------


def _render_rustic(
    data_url, design_size, org_name, org_logo_url, colors, table_name, custom_text
):
    """
    RUSTIC: warm kraft-paper tones, textured decorative borders,
    earthy color palette, handwritten-style text vibe.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import mm

    page_w, page_h = _get_page_dims(design_size)
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=(page_w, page_h))

    bg = colors["background"]
    primary = colors["primary"]
    secondary = colors["secondary"]
    colors["text"]
    accent = colors["accent"]

    # -- Kraft-paper background
    c.setFillColor(HexColor(bg))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # -- Outer decorative border (thick)
    bw = min(page_w, page_h) * 0.04
    c.setStrokeColor(HexColor(primary))
    c.setLineWidth(2.5)
    c.rect(bw, bw, page_w - 2 * bw, page_h - 2 * bw, fill=0, stroke=1)

    # -- Inner dashed decorative border
    inner_bw = bw + min(page_w, page_h) * 0.02
    c.setStrokeColor(HexColor(secondary))
    c.setLineWidth(0.75)
    c.setDash(4, 3)
    c.rect(
        inner_bw,
        inner_bw,
        page_w - 2 * inner_bw,
        page_h - 2 * inner_bw,
        fill=0,
        stroke=1,
    )
    c.setDash()  # Reset dash

    # -- Decorative top flourish lines
    fl_y = page_h * 0.88
    fl_half = page_w * 0.25
    c.setStrokeColor(HexColor(accent))
    c.setLineWidth(1)
    c.line(page_w / 2 - fl_half, fl_y, page_w / 2 - page_w * 0.04, fl_y)
    c.line(page_w / 2 + page_w * 0.04, fl_y, page_w / 2 + fl_half, fl_y)
    # Small diamond at center
    d_size = min(page_w, page_h) * 0.015
    p = c.beginPath()
    cx, cy = page_w / 2, fl_y
    p.moveTo(cx, cy + d_size)
    p.lineTo(cx + d_size, cy)
    p.lineTo(cx, cy - d_size)
    p.lineTo(cx - d_size, cy)
    p.close()
    c.setFillColor(HexColor(accent))
    c.drawPath(p, fill=1, stroke=0)

    # -- Logo
    logo_pil = _load_logo_pil(org_logo_url)
    if logo_pil:
        logo_display = min(page_w * 0.2, 50 * mm)
        logo_reader = _pil_to_reader(logo_pil)
        c.drawImage(
            logo_reader,
            (page_w - logo_display) / 2,
            page_h * 0.88 + min(page_w, page_h) * 0.02,
            logo_display,
            logo_display,
            preserveAspectRatio=True,
            anchor="c",
        )

    # -- Organization name
    if org_name:
        name_y = page_h * 0.80
        font_size = min(page_w * 0.065, 28)
        c.setFillColor(HexColor(primary))
        c.setFont("Times-BoldItalic", font_size)
        c.drawCentredString(page_w / 2, name_y, org_name)

    # -- Bottom flourish above instruction
    fl2_y = page_h * 0.76
    c.setStrokeColor(HexColor(secondary))
    c.setLineWidth(0.5)
    c.line(page_w * 0.3, fl2_y, page_w * 0.7, fl2_y)

    # -- QR code
    qr_display = min(page_w, page_h) * 0.45
    qr_px = max(512, int(qr_display / mm * 3))
    qr_pil = _make_qr_pil(data_url, qr_px, logo_url=org_logo_url)
    qr_reader = _pil_to_reader(qr_pil)

    qr_x = (page_w - qr_display) / 2
    qr_y = page_h * 0.32
    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        qr_display,
        qr_display,
        preserveAspectRatio=True,
        anchor="c",
    )

    # -- Table name
    if table_name:
        t_y = qr_y - page_h * 0.05
        t_size = min(page_w * 0.05, 20)
        c.setFillColor(HexColor(primary))
        c.setFont("Times-Bold", t_size)
        c.drawCentredString(page_w / 2, t_y, table_name)

    # -- Instruction
    instruction = custom_text or _default_instruction(table_name)
    instr_y = page_h * 0.22 if not table_name else page_h * 0.18
    instr_size = min(page_w * 0.035, 14)
    c.setFillColor(HexColor(secondary))
    c.setFont("Times-Italic", instr_size)
    c.drawCentredString(page_w / 2, instr_y, instruction)

    # -- Footer
    _draw_footer(c, page_w, page_h, color=_lighten(primary, 0.4), font_size=7)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -------------------------------------------------------------------------
# VIBRANT template
# -------------------------------------------------------------------------


def _render_vibrant(
    data_url, design_size, org_name, org_logo_url, colors, table_name, custom_text
):
    """
    VIBRANT: bold brand colors, colored QR frame, prominent logo,
    strong visual impact.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import mm

    page_w, page_h = _get_page_dims(design_size)
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=(page_w, page_h))

    bg = colors["background"]
    primary = colors["primary"]
    secondary = colors["secondary"]
    colors["text"]
    accent = colors["accent"]

    # -- Background
    c.setFillColor(HexColor(bg))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # -- Top colored band
    band_h = page_h * 0.12
    c.setFillColor(HexColor(primary))
    c.rect(0, page_h - band_h, page_w, band_h, fill=1, stroke=0)

    # -- Bottom colored band
    c.setFillColor(HexColor(primary))
    c.rect(0, 0, page_w, band_h * 0.6, fill=1, stroke=0)

    # -- Large logo prominently centered at top
    logo_pil = _load_logo_pil(org_logo_url)
    logo_bottom_y = page_h * 0.75
    if logo_pil:
        logo_display = min(page_w * 0.3, 70 * mm)
        logo_reader = _pil_to_reader(logo_pil)
        logo_x = (page_w - logo_display) / 2
        logo_y = page_h * 0.82
        c.drawImage(
            logo_reader,
            logo_x,
            logo_y,
            logo_display,
            logo_display,
            preserveAspectRatio=True,
            anchor="c",
        )
        logo_bottom_y = logo_y - logo_display * 0.1

    # -- Organization name (bold, colored)
    if org_name:
        name_y = logo_bottom_y - page_h * 0.01
        font_size = min(page_w * 0.07, 30)
        c.setFillColor(HexColor(primary))
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(page_w / 2, name_y, org_name)

    # -- Colored QR frame
    qr_display = min(page_w, page_h) * 0.45
    frame_pad = qr_display * 0.08
    frame_size = qr_display + frame_pad * 2

    frame_x = (page_w - frame_size) / 2
    frame_y = page_h * 0.28
    _draw_rounded_rect(
        c,
        frame_x,
        frame_y,
        frame_size,
        frame_size,
        radius=frame_size * 0.06,
        fill_color=_lighten(primary, 0.85),
        stroke_color=primary,
        stroke_width=2.5,
    )

    # -- QR code inside frame
    qr_px = max(512, int(qr_display / mm * 3))
    qr_pil = _make_qr_pil(data_url, qr_px, logo_url=org_logo_url)
    qr_reader = _pil_to_reader(qr_pil)
    qr_x = frame_x + frame_pad
    qr_y = frame_y + frame_pad
    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        qr_display,
        qr_display,
        preserveAspectRatio=True,
        anchor="c",
    )

    # -- Table name (bold accent color)
    if table_name:
        t_y = frame_y - page_h * 0.04
        t_size = min(page_w * 0.055, 22)
        c.setFillColor(HexColor(accent))
        c.setFont("Helvetica-Bold", t_size)
        c.drawCentredString(page_w / 2, t_y, table_name)

    # -- Instruction text
    instruction = custom_text or _default_instruction(table_name)
    instr_y = page_h * 0.18 if not table_name else page_h * 0.14
    instr_size = min(page_w * 0.038, 15)
    c.setFillColor(HexColor(secondary))
    c.setFont("Helvetica-Bold", instr_size)
    c.drawCentredString(page_w / 2, instr_y, instruction)

    # -- Footer (in the bottom band, white text)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica", min(page_w * 0.025, 9))
    c.drawCentredString(page_w / 2, band_h * 0.6 * 0.35, "e-menum.net")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -------------------------------------------------------------------------
# MINIMAL template
# -------------------------------------------------------------------------


def _render_minimal(
    data_url, design_size, org_name, org_logo_url, colors, table_name, custom_text
):
    """
    MINIMAL: ultra-clean, just QR + small text, maximum whitespace,
    no decorative elements.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import mm

    page_w, page_h = _get_page_dims(design_size)
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=(page_w, page_h))

    bg = colors["background"]
    primary = colors["primary"]
    text_col = colors["text"]
    secondary = colors["secondary"]

    # -- Clean background
    c.setFillColor(HexColor(bg))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # -- Organization name (small, at top center)
    top_element_y = page_h * 0.85
    if org_name:
        name_size = min(page_w * 0.04, 16)
        c.setFillColor(HexColor(text_col))
        c.setFont("Helvetica", name_size)
        c.drawCentredString(page_w / 2, top_element_y, org_name)

    # -- Small logo above org name (if available)
    logo_pil = _load_logo_pil(org_logo_url)
    if logo_pil:
        logo_display = min(page_w * 0.12, 30 * mm)
        logo_reader = _pil_to_reader(logo_pil)
        c.drawImage(
            logo_reader,
            (page_w - logo_display) / 2,
            top_element_y + page_h * 0.03,
            logo_display,
            logo_display,
            preserveAspectRatio=True,
            anchor="c",
        )

    # -- QR code (large, truly centered)
    qr_display = min(page_w, page_h) * 0.50
    qr_px = max(512, int(qr_display / mm * 3))
    qr_pil = _make_qr_pil(data_url, qr_px, logo_url=org_logo_url)
    qr_reader = _pil_to_reader(qr_pil)

    qr_x = (page_w - qr_display) / 2
    qr_y = (page_h - qr_display) / 2
    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        qr_display,
        qr_display,
        preserveAspectRatio=True,
        anchor="c",
    )

    # -- Table name (small, below QR)
    below_qr_y = qr_y - page_h * 0.04
    if table_name:
        t_size = min(page_w * 0.04, 16)
        c.setFillColor(HexColor(primary))
        c.setFont("Helvetica-Bold", t_size)
        c.drawCentredString(page_w / 2, below_qr_y, table_name)
        below_qr_y -= page_h * 0.03

    # -- Instruction (very small)
    instruction = custom_text or _default_instruction(table_name)
    instr_size = min(page_w * 0.028, 11)
    c.setFillColor(HexColor(secondary))
    c.setFont("Helvetica", instr_size)
    c.drawCentredString(page_w / 2, below_qr_y, instruction)

    # -- Footer
    _draw_footer(c, page_w, page_h, color=_lighten(text_col, 0.6), font_size=7)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# =========================================================================
# Template renderer dispatch
# =========================================================================

_TEMPLATE_RENDERERS = {
    "ELEGANT": _render_elegant,
    "MODERN": _render_modern,
    "RUSTIC": _render_rustic,
    "VIBRANT": _render_vibrant,
    "MINIMAL": _render_minimal,
}
