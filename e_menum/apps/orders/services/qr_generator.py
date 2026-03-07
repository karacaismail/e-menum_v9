"""
QR Code generation service for the Orders application.

Generates QR code images in multiple formats (PNG, SVG, JPEG, PDF),
supports logo overlay, and creates print-ready designs for table cards
and posters in various standard sizes.

Usage:
    from apps.orders.services.qr_generator import QRGeneratorService

    # Generate and save QR code image for a QRCode instance
    image_url = QRGeneratorService.generate_and_save(qr_code_instance)

    # Generate QR code as BytesIO (for direct download)
    buffer = QRGeneratorService.generate_qr_image("https://example.com/m/menu-slug/")

    # Generate QR with organization logo overlay
    buffer = QRGeneratorService.generate_qr_with_logo(url, logo_path_or_url="/path/to/logo.png")

    # Generate SVG format
    svg_str = QRGeneratorService.generate_qr_svg(url, size=512)

    # Generate print-ready PDF design
    pdf = QRGeneratorService.generate_print_design(url, design_size="A4", org_name="Cafe")

    # Download QR for a model instance in any format
    buffer = QRGeneratorService.download_qr(qr_code, format="png", size=512)
"""

import io
import logging
import os
import uuid

import qrcode
import qrcode.image.svg
import requests
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageDraw, ImageFont

from django.conf import settings

logger = logging.getLogger(__name__)


# Print design size definitions in mm (width, height)
PRINT_SIZES = {
    '10x20cm': (100, 200),
    'A5': (148, 210),
    'A4': (210, 297),
    '15x30cm': (150, 300),
    '20x40cm': (200, 400),
}


class QRGeneratorService:
    """Service for generating QR code images in multiple formats."""

    # Default QR code settings
    DEFAULT_SIZE = 400  # pixels
    DEFAULT_BORDER = 2  # quiet zone modules
    DEFAULT_BOX_SIZE = 10  # pixels per module
    QR_MEDIA_SUBDIR = 'qr_codes'

    # -------------------------------------------------------------------------
    # Core QR generation (PNG)
    # -------------------------------------------------------------------------

    @classmethod
    def _make_qr_pil(cls, data_url, size=None):
        """Generate a raw QR code as a PIL Image (no label, no logo)."""
        size = size or cls.DEFAULT_SIZE

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=cls.DEFAULT_BOX_SIZE,
            border=cls.DEFAULT_BORDER,
        )
        qr.add_data(data_url)
        qr.make(fit=True)

        try:
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
            ).convert('RGB')
        except Exception:
            img = qr.make_image(fill_color='black', back_color='white').convert('RGB')

        img = img.resize((size, size), Image.LANCZOS)
        return img

    @classmethod
    def generate_qr_image(cls, data_url, size=None, with_logo=False):
        """
        Generate a QR code image as a BytesIO buffer (PNG).

        Args:
            data_url: The URL/data to encode in the QR code
            size: Output image size in pixels (default: 400)
            with_logo: Whether to add e-menum branding

        Returns:
            io.BytesIO: PNG image buffer
        """
        size = size or cls.DEFAULT_SIZE
        img = cls._make_qr_pil(data_url, size=size)

        # Add bottom label
        img = cls._add_label(img, data_url)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer

    # -------------------------------------------------------------------------
    # Logo overlay
    # -------------------------------------------------------------------------

    @classmethod
    def _load_logo(cls, logo_path_or_url):
        """Load a logo from a local file path or URL. Returns PIL Image or None."""
        try:
            if logo_path_or_url.startswith(('http://', 'https://')):
                resp = requests.get(logo_path_or_url, timeout=10)
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content)).convert('RGBA')
            else:
                return Image.open(logo_path_or_url).convert('RGBA')
        except Exception as e:
            logger.warning("Could not load logo from %s: %s", logo_path_or_url, e)
            return None

    @classmethod
    def _overlay_logo(cls, qr_img, logo_img, logo_ratio=0.25):
        """Paste a logo in the center of a QR image with a white background pad."""
        qr_w, qr_h = qr_img.size
        logo_max = int(min(qr_w, qr_h) * logo_ratio)

        # Resize logo maintaining aspect ratio
        logo_img.thumbnail((logo_max, logo_max), Image.LANCZOS)
        logo_w, logo_h = logo_img.size

        # White background circle/square behind logo
        pad = 8
        bg_size = (logo_w + pad * 2, logo_h + pad * 2)
        bg = Image.new('RGBA', bg_size, (255, 255, 255, 255))

        # Center logo on background
        bg.paste(logo_img, (pad, pad), logo_img)

        # Center on QR
        pos = ((qr_w - bg_size[0]) // 2, (qr_h - bg_size[1]) // 2)

        # Convert QR to RGBA if needed
        if qr_img.mode != 'RGBA':
            qr_img = qr_img.convert('RGBA')

        qr_img.paste(bg, pos, bg)
        return qr_img.convert('RGB')

    @classmethod
    def generate_qr_with_logo(cls, data_url, logo_path_or_url, size=512):
        """
        Generate a QR code PNG with a logo overlay in the center.

        Args:
            data_url: URL to encode
            logo_path_or_url: Local file path or HTTP URL to logo image
            size: Output size in pixels

        Returns:
            io.BytesIO: PNG image buffer with logo overlay
        """
        img = cls._make_qr_pil(data_url, size=size)

        logo_img = cls._load_logo(logo_path_or_url)
        if logo_img:
            img = cls._overlay_logo(img, logo_img)

        img = cls._add_label(img, data_url)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer

    # -------------------------------------------------------------------------
    # SVG format
    # -------------------------------------------------------------------------

    @classmethod
    def generate_qr_svg(cls, data_url, size=512):
        """
        Generate a QR code as an SVG XML string.

        Args:
            data_url: URL to encode
            size: Logical size (viewBox dimension)

        Returns:
            str: SVG XML string
        """
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=cls.DEFAULT_BOX_SIZE,
            border=cls.DEFAULT_BORDER,
        )
        qr.add_data(data_url)
        qr.make(fit=True)

        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(image_factory=factory)

        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        svg_content = buffer.read().decode('utf-8')
        return svg_content

    # -------------------------------------------------------------------------
    # JPEG format
    # -------------------------------------------------------------------------

    @classmethod
    def generate_qr_jpg(cls, data_url, size=512, quality=90):
        """
        Generate a QR code as a JPEG BytesIO buffer.

        Args:
            data_url: URL to encode
            size: Output size in pixels
            quality: JPEG quality (1-100)

        Returns:
            io.BytesIO: JPEG image buffer
        """
        img = cls._make_qr_pil(data_url, size=size)
        img = cls._add_label(img, data_url)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        return buffer

    # -------------------------------------------------------------------------
    # Multi-format batch
    # -------------------------------------------------------------------------

    @classmethod
    def generate_qr_multiformat(cls, data_url, formats=None, sizes=None):
        """
        Generate QR codes in multiple formats and sizes.

        Args:
            data_url: URL to encode
            formats: List of formats ('png', 'svg', 'jpg', 'pdf')
            sizes: List of pixel sizes

        Returns:
            dict: {format_str: {size_int: BytesIO or str}}
        """
        formats = formats or ['png', 'svg', 'jpg', 'pdf']
        sizes = sizes or [128, 256, 512, 1024]

        result = {}
        for fmt in formats:
            result[fmt] = {}
            for sz in sizes:
                if fmt == 'png':
                    result[fmt][sz] = cls.generate_qr_image(data_url, size=sz)
                elif fmt == 'svg':
                    result[fmt][sz] = cls.generate_qr_svg(data_url, size=sz)
                elif fmt == 'jpg':
                    result[fmt][sz] = cls.generate_qr_jpg(data_url, size=sz)
                elif fmt == 'pdf':
                    result[fmt][sz] = cls._generate_single_qr_pdf(data_url, size=sz)

        return result

    @classmethod
    def _generate_single_qr_pdf(cls, data_url, size=512):
        """Generate a minimal single-page PDF containing the QR code image."""
        img = cls._make_qr_pil(data_url, size=size)
        img = cls._add_label(img, data_url)

        # Convert PIL image to PDF via Pillow
        buffer = io.BytesIO()
        rgb_img = img.convert('RGB')
        rgb_img.save(buffer, format='PDF', resolution=150)
        buffer.seek(0)
        return buffer

    # -------------------------------------------------------------------------
    # Print-ready design PDFs
    # -------------------------------------------------------------------------

    @classmethod
    def generate_print_design(cls, data_url, design_size='A4', orientation='portrait',
                              org_name='', org_logo_url=None):
        """
        Generate a print-ready PDF with QR code, branding, and instructions.

        Supported design_size: '10x20cm', 'A5', 'A4', '15x30cm', '20x40cm'

        Args:
            data_url: URL to encode in QR
            design_size: Paper size key
            orientation: 'portrait' or 'landscape'
            org_name: Organization name to display
            org_logo_url: Optional URL to organization logo

        Returns:
            io.BytesIO: PDF buffer
        """
        from reportlab.lib.pagesizes import mm
        from reportlab.lib.colors import HexColor
        from reportlab.pdfgen import canvas as pdf_canvas

        # Get dimensions in mm
        size_mm = PRINT_SIZES.get(design_size, PRINT_SIZES['A4'])
        w_mm, h_mm = size_mm

        if orientation == 'landscape':
            w_mm, h_mm = h_mm, w_mm

        page_w = w_mm * mm
        page_h = h_mm * mm

        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=(page_w, page_h))

        # Background
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        # QR code size: 60% of the smaller dimension
        qr_display = min(page_w, page_h) * 0.6
        qr_px = max(512, int(qr_display / mm * 3))  # High DPI

        # Generate QR image (with logo if available)
        if org_logo_url:
            logo_img = cls._load_logo(org_logo_url)
        else:
            logo_img = None

        qr_pil = cls._make_qr_pil(data_url, size=qr_px)
        if logo_img:
            qr_pil = cls._overlay_logo(qr_pil, logo_img, logo_ratio=0.22)

        # Convert QR PIL to reportlab image
        qr_buf = io.BytesIO()
        qr_pil.save(qr_buf, format='PNG')
        qr_buf.seek(0)

        from reportlab.lib.utils import ImageReader
        qr_reader = ImageReader(qr_buf)

        # Center QR on page
        qr_x = (page_w - qr_display) / 2
        qr_y = page_h * 0.35

        c.drawImage(qr_reader, qr_x, qr_y, qr_display, qr_display,
                     preserveAspectRatio=True, anchor='c')

        # Organization name
        if org_name:
            c.setFillColor(HexColor('#1F2937'))
            font_size = min(page_w * 0.06, 28)
            c.setFont('Helvetica-Bold', font_size)
            c.drawCentredString(page_w / 2, qr_y + qr_display + page_h * 0.05, org_name)

        # "Scan to view menu" instruction
        c.setFillColor(HexColor('#6B7280'))
        instr_size = min(page_w * 0.04, 16)
        c.setFont('Helvetica', instr_size)
        c.drawCentredString(page_w / 2, qr_y - page_h * 0.04, 'Menuyu goruntule')

        # Branding footer
        c.setFillColor(HexColor('#9CA3AF'))
        footer_size = min(page_w * 0.028, 10)
        c.setFont('Helvetica', footer_size)
        c.drawCentredString(page_w / 2, page_h * 0.04, 'e-menum.net')

        # Organization logo at top if available
        if logo_img:
            logo_display = min(page_w * 0.2, 60 * mm)
            logo_buf = io.BytesIO()
            logo_img.convert('RGB').save(logo_buf, format='PNG')
            logo_buf.seek(0)
            logo_reader = ImageReader(logo_buf)

            logo_x = (page_w - logo_display) / 2
            logo_y = page_h * 0.88
            c.drawImage(logo_reader, logo_x, logo_y, logo_display, logo_display,
                         preserveAspectRatio=True, anchor='c')

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    # -------------------------------------------------------------------------
    # Download helpers (model-aware convenience methods)
    # -------------------------------------------------------------------------

    @classmethod
    def download_qr(cls, qr_code, format='png', size=512):
        """
        Generate a downloadable QR code for a QRCode model instance.

        Args:
            qr_code: QRCode model instance
            format: 'png', 'svg', 'jpg', or 'pdf'
            size: Output size in pixels

        Returns:
            io.BytesIO or str: The generated QR code data
        """
        target_url = cls.get_target_url(qr_code)

        if format == 'png':
            return cls.generate_qr_image(target_url, size=size)
        elif format == 'svg':
            svg_str = cls.generate_qr_svg(target_url, size=size)
            buf = io.BytesIO(svg_str.encode('utf-8'))
            buf.seek(0)
            return buf
        elif format == 'jpg':
            return cls.generate_qr_jpg(target_url, size=size)
        elif format == 'pdf':
            return cls._generate_single_qr_pdf(target_url, size=size)
        else:
            return cls.generate_qr_image(target_url, size=size)

    @classmethod
    def download_print_design(cls, qr_code, design_size='A4'):
        """
        Generate a downloadable print-ready PDF for a QRCode instance.

        Automatically uses the organization's name and logo.

        Args:
            qr_code: QRCode model instance
            design_size: Paper size key ('10x20cm', 'A5', 'A4', '15x30cm', '20x40cm')

        Returns:
            io.BytesIO: PDF buffer
        """
        target_url = cls.get_target_url(qr_code)
        org = qr_code.organization

        org_name = getattr(org, 'name', '') if org else ''
        org_logo_url = getattr(org, 'logo', None) if org else None

        return cls.generate_print_design(
            data_url=target_url,
            design_size=design_size,
            orientation='portrait',
            org_name=org_name,
            org_logo_url=org_logo_url,
        )

    # -------------------------------------------------------------------------
    # Label helper
    # -------------------------------------------------------------------------

    @classmethod
    def _add_label(cls, img, data_url):
        """Add a small label at the bottom of the QR image."""
        try:
            label = 'e-menum.net'

            label_height = 30
            new_img = Image.new('RGB', (img.width, img.height + label_height), 'white')
            new_img.paste(img, (0, 0))

            draw = ImageDraw.Draw(new_img)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except (IOError, OSError):
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            x = (new_img.width - text_width) // 2
            y = img.height + (label_height - (bbox[3] - bbox[1])) // 2

            draw.text((x, y), label, fill='#333333', font=font)

            return new_img
        except Exception as e:
            logger.warning("Could not add label to QR image: %s", e)
            return img

    # -------------------------------------------------------------------------
    # URL + persistence
    # -------------------------------------------------------------------------

    @classmethod
    def get_target_url(cls, qr_code):
        """Build the target URL for a QR code based on its type."""
        from django.conf import settings

        site_url = getattr(settings, 'SITE_URL', '')
        if not site_url:
            site_domain = getattr(settings, 'SITE_DOMAIN', 'e-menum.net')
            site_url = f'https://{site_domain}'

        if qr_code.redirect_url:
            return qr_code.redirect_url

        return f'{site_url}/q/{qr_code.code}/'

    @classmethod
    def generate_and_save(cls, qr_code, force=False):
        """
        Generate a QR code image and save it to the media directory.
        Updates the QRCode instance's qr_image_url field.

        Returns:
            str: The media URL of the saved QR image, or None on failure
        """
        if qr_code.qr_image_url and not force:
            logger.debug("QR code %s already has an image, skipping", qr_code.code)
            return qr_code.qr_image_url

        try:
            target_url = cls.get_target_url(qr_code)
            buffer = cls.generate_qr_image(target_url, size=cls.DEFAULT_SIZE)

            filename = f'qr_{qr_code.code}_{uuid.uuid4().hex[:8]}.png'
            relative_path = os.path.join(cls.QR_MEDIA_SUBDIR, filename)
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

            with open(absolute_path, 'wb') as f:
                f.write(buffer.read())

            media_url = f'{settings.MEDIA_URL}{relative_path}'

            qr_code.qr_image_url = media_url
            if not qr_code.short_url:
                qr_code.short_url = target_url

            qr_code.save(update_fields=['qr_image_url', 'short_url', 'updated_at'])

            logger.info(
                "QR code image generated: code=%s, path=%s",
                qr_code.code, relative_path
            )

            return media_url

        except Exception as e:
            logger.error(
                "Failed to generate QR code image for %s: %s",
                qr_code.code, str(e)
            )
            return None

    @classmethod
    def generate_bulk(cls, qr_codes, force=False):
        """Generate QR code images for multiple QRCode instances."""
        results = {}
        for qr_code in qr_codes:
            results[str(qr_code.id)] = cls.generate_and_save(qr_code, force=force)
        return results
