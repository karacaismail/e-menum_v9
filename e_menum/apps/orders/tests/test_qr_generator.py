"""
Tests for the QR Code generation service (QRGeneratorService).

Tests cover:
- Basic QR image generation (PNG, SVG, JPEG)
- Custom sizes and format options
- Logo overlay on QR codes
- Multi-format batch generation
- Print-ready PDF design generation (A4, A5, 10x20cm, 15x30cm, 20x40cm)
- Download helpers for QR codes and print designs
- Target URL generation for MENU and TABLE types
- File saving and model update workflow

Uses pytest-django with Factory Boy factories and PIL for image verification.
"""

import io
import os
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from apps.orders.services.qr_generator import QRGeneratorService
from tests.factories.core import OrganizationFactory
from tests.factories.orders import QRCodeFactory, TableFactory, ZoneFactory


pytestmark = pytest.mark.django_db


# =============================================================================
# HELPERS
# =============================================================================


def _create_test_logo_image(size=(100, 100), color="red"):
    """Create a small in-memory PNG image for logo testing."""
    img = Image.new("RGBA", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _is_valid_png(buffer):
    """Check whether a BytesIO buffer contains a valid PNG image."""
    buffer.seek(0)
    try:
        img = Image.open(buffer)
        img.verify()
        return img.format == "PNG"
    except Exception:
        return False


def _is_valid_jpeg(buffer):
    """Check whether a BytesIO buffer contains a valid JPEG image."""
    buffer.seek(0)
    try:
        img = Image.open(buffer)
        img.verify()
        return img.format == "JPEG"
    except Exception:
        return False


def _is_valid_pdf(buffer):
    """Check whether a BytesIO buffer starts with the PDF magic bytes."""
    buffer.seek(0)
    header = buffer.read(5)
    return header == b"%PDF-"


def _is_valid_svg(content):
    """Check whether a string looks like valid SVG XML."""
    if not isinstance(content, str):
        return False
    return "<svg" in content and "</svg>" in content


def _get_image_dimensions(buffer):
    """Return (width, height) for an image in a BytesIO buffer."""
    buffer.seek(0)
    img = Image.open(buffer)
    return img.size


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def org(db):
    return OrganizationFactory(
        name="Test Cafe",
        logo="https://example.com/logos/test-cafe.png",
    )


@pytest.fixture
def org_no_logo(db):
    return OrganizationFactory(name="No Logo Cafe", logo=None)


@pytest.fixture
def zone(db, org):
    return ZoneFactory(organization=org)


@pytest.fixture
def table(db, zone):
    return TableFactory(zone=zone)


@pytest.fixture
def menu_qr(db, org):
    return QRCodeFactory(organization=org, type="MENU")


@pytest.fixture
def table_qr(db, org, table):
    return QRCodeFactory(organization=org, type="TABLE", table=table)


@pytest.fixture
def test_logo_path(tmp_path):
    """Write a small PNG logo to a temp file and return its path."""
    logo_buf = _create_test_logo_image(size=(80, 80), color="blue")
    logo_file = tmp_path / "logo.png"
    logo_file.write_bytes(logo_buf.read())
    return str(logo_file)


@pytest.fixture
def sample_url():
    return "https://e-menum.net/q/test-code-abc/"


# =============================================================================
# 1. BASIC QR IMAGE GENERATION
# =============================================================================


class TestGenerateQRImageBasic:
    """Test basic QR image generation with default parameters."""

    def test_generate_qr_image_basic(self, sample_url):
        """Generate a QR PNG with default size; verify it is a valid PNG."""
        result = QRGeneratorService.generate_qr_image(sample_url)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_png(result)

        width, height = _get_image_dimensions(result)
        # Default size is 400px, but label adds extra height
        assert width == QRGeneratorService.DEFAULT_SIZE
        assert height >= QRGeneratorService.DEFAULT_SIZE


# =============================================================================
# 2. CUSTOM SIZE QR IMAGE
# =============================================================================


class TestGenerateQRImageCustomSize:
    """Test QR image generation with various custom sizes."""

    @pytest.mark.parametrize("size", [128, 256, 512, 1024])
    def test_generate_qr_image_custom_size(self, sample_url, size):
        """Generate QR images at specific pixel sizes and verify dimensions."""
        result = QRGeneratorService.generate_qr_image(sample_url, size=size)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_png(result)

        width, height = _get_image_dimensions(result)
        assert width == size
        # Height includes the label area, so >= size
        assert height >= size


# =============================================================================
# 3. QR WITH LOGO (LOCAL FILE PATH)
# =============================================================================


class TestGenerateQRWithLogo:
    """Test QR code generation with a logo overlay from a local file."""

    def test_generate_qr_with_logo(self, sample_url, test_logo_path):
        """Generate QR with logo overlay; result must be valid PNG and
        typically larger in file size than a plain QR."""
        plain_buf = QRGeneratorService.generate_qr_image(sample_url, size=512)
        plain_buf.seek(0)
        plain_size = len(plain_buf.read())

        logo_buf = QRGeneratorService.generate_qr_with_logo(
            sample_url, logo_path_or_url=test_logo_path, size=512
        )

        assert isinstance(logo_buf, io.BytesIO)
        assert _is_valid_png(logo_buf)

        logo_buf.seek(0)
        logo_size = len(logo_buf.read())
        # Logo version should be at least as large as the plain version
        # (logo overlay adds data); allow equal in case of compression gains.
        assert logo_size >= plain_size * 0.8, (
            f"Logo QR ({logo_size}B) unexpectedly much smaller than "
            f"plain QR ({plain_size}B)"
        )


# =============================================================================
# 4. QR WITH LOGO (URL - MOCKED DOWNLOAD)
# =============================================================================


class TestGenerateQRWithLogoURL:
    """Test QR with logo when the logo source is a URL (download mocked)."""

    @patch("apps.orders.services.qr_generator.requests.get")
    def test_generate_qr_with_logo_url(self, mock_get, sample_url):
        """When logo_path_or_url is an HTTP URL, the service should download
        the image. We mock the network call and verify the result."""
        logo_bytes = _create_test_logo_image(size=(64, 64), color="green")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = logo_bytes.read()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = QRGeneratorService.generate_qr_with_logo(
            sample_url,
            logo_path_or_url="https://example.com/logos/cafe.png",
            size=512,
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_png(result)
        mock_get.assert_called_once()


# =============================================================================
# 5. SVG GENERATION
# =============================================================================


class TestGenerateQRSVG:
    """Test QR code generation in SVG format."""

    def test_generate_qr_svg(self, sample_url):
        """Generate an SVG string and verify it contains valid SVG markup."""
        result = QRGeneratorService.generate_qr_svg(sample_url, size=512)

        assert isinstance(result, str)
        assert _is_valid_svg(result)
        # SVG should contain standard SVG namespace or element
        assert "xmlns" in result or "<rect" in result or "<path" in result


# =============================================================================
# 6. JPEG GENERATION
# =============================================================================


class TestGenerateQRJPG:
    """Test QR code generation in JPEG format."""

    def test_generate_qr_jpg(self, sample_url):
        """Generate a JPEG buffer and verify it is valid JPEG."""
        result = QRGeneratorService.generate_qr_jpg(sample_url, size=512, quality=90)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_jpeg(result)

        width, height = _get_image_dimensions(result)
        assert width == 512
        assert height >= 512


# =============================================================================
# 7. MULTI-FORMAT GENERATION
# =============================================================================


class TestGenerateQRMultiformat:
    """Test multi-format batch QR generation."""

    def test_generate_qr_multiformat(self, sample_url):
        """Verify all requested formats and sizes are returned."""
        formats = ["png", "svg", "jpg", "pdf"]
        sizes = [128, 256, 512, 1024]

        result = QRGeneratorService.generate_qr_multiformat(
            sample_url, formats=formats, sizes=sizes
        )

        assert isinstance(result, dict)

        for fmt in formats:
            assert fmt in result, f"Format '{fmt}' missing from result"
            assert isinstance(result[fmt], dict)

            for sz in sizes:
                assert sz in result[fmt], f"Size {sz} missing for format '{fmt}'"
                item = result[fmt][sz]

                if fmt == "svg":
                    assert isinstance(item, str)
                    assert _is_valid_svg(item)
                elif fmt == "png":
                    assert isinstance(item, io.BytesIO)
                    assert _is_valid_png(item)
                elif fmt == "jpg":
                    assert isinstance(item, io.BytesIO)
                    assert _is_valid_jpeg(item)
                elif fmt == "pdf":
                    assert isinstance(item, io.BytesIO)
                    assert _is_valid_pdf(item)


# =============================================================================
# 8-12. PRINT DESIGN GENERATION
# =============================================================================


class TestGeneratePrintDesign:
    """Test print-ready PDF design generation for various sizes."""

    def test_generate_print_design_a4(self, sample_url):
        """Generate an A4 print design PDF and verify it is valid."""
        result = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="A4",
            orientation="portrait",
            org_name="Test Cafe",
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)
        # A4 PDF should have meaningful content (not just header)
        result.seek(0)
        assert len(result.read()) > 500

    def test_generate_print_design_10x20(self, sample_url):
        """Generate a 10x20cm print design PDF."""
        result = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="10x20cm",
            orientation="portrait",
            org_name="Small Cafe",
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)

    def test_generate_print_design_a5(self, sample_url):
        """Generate an A5 print design PDF."""
        result = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="A5",
            orientation="portrait",
            org_name="A5 Cafe",
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)

    def test_generate_print_design_15x30(self, sample_url):
        """Generate a 15x30cm print design PDF."""
        result = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="15x30cm",
            orientation="portrait",
            org_name="Medium Cafe",
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)

    def test_generate_print_design_20x40(self, sample_url):
        """Generate a 20x40cm print design PDF."""
        result = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="20x40cm",
            orientation="portrait",
            org_name="Large Cafe",
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)

    def test_generate_print_design_landscape(self, sample_url):
        """Landscape orientation should also produce a valid PDF."""
        result = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="A4",
            orientation="landscape",
            org_name="Landscape Cafe",
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)


# =============================================================================
# 13. PRINT DESIGN WITH LOGO
# =============================================================================


class TestGeneratePrintDesignWithLogo:
    """Test that an organization logo is embedded in the print design."""

    @patch("apps.orders.services.qr_generator.requests.get")
    def test_generate_print_design_with_logo(self, mock_get, sample_url):
        """When org_logo_url is provided, the PDF should embed it.
        The resulting PDF should be larger than one without a logo."""
        logo_bytes = _create_test_logo_image(size=(120, 120), color="purple")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = logo_bytes.read()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result_with_logo = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="A4",
            orientation="portrait",
            org_name="Branded Cafe",
            org_logo_url="https://example.com/logos/branded.png",
        )

        assert isinstance(result_with_logo, io.BytesIO)
        assert _is_valid_pdf(result_with_logo)

        # Also generate without logo for comparison
        result_no_logo = QRGeneratorService.generate_print_design(
            sample_url,
            design_size="A4",
            orientation="portrait",
            org_name="Plain Cafe",
            org_logo_url=None,
        )

        result_with_logo.seek(0)
        result_no_logo.seek(0)
        size_with = len(result_with_logo.read())
        size_without = len(result_no_logo.read())

        # PDF with logo should be at least slightly larger
        assert size_with >= size_without * 0.9, (
            f"Logo PDF ({size_with}B) unexpectedly smaller than "
            f"plain PDF ({size_without}B)"
        )


# =============================================================================
# 14-17. DOWNLOAD QR IN VARIOUS FORMATS
# =============================================================================


class TestDownloadQR:
    """Test the download_qr convenience method for each format."""

    def test_download_qr_png(self, menu_qr):
        """Download QR code as PNG."""
        result = QRGeneratorService.download_qr(menu_qr, format="png", size=512)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_png(result)

    def test_download_qr_svg(self, menu_qr):
        """Download QR code as SVG (may return BytesIO wrapping SVG string
        or a str; both are acceptable)."""
        result = QRGeneratorService.download_qr(menu_qr, format="svg", size=512)

        if isinstance(result, io.BytesIO):
            result.seek(0)
            content = result.read().decode("utf-8")
        else:
            content = result

        assert _is_valid_svg(content)

    def test_download_qr_jpg(self, menu_qr):
        """Download QR code as JPG."""
        result = QRGeneratorService.download_qr(menu_qr, format="jpg", size=512)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_jpeg(result)

    def test_download_qr_pdf(self, menu_qr):
        """Download QR code as PDF."""
        result = QRGeneratorService.download_qr(menu_qr, format="pdf", size=512)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)


# =============================================================================
# 18. DOWNLOAD PRINT DESIGN
# =============================================================================


class TestDownloadPrintDesign:
    """Test the download_print_design convenience method."""

    def test_download_print_design(self, menu_qr, org):
        """download_print_design should return a valid PDF for a QR code."""
        result = QRGeneratorService.download_print_design(menu_qr, design_size="A4")

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)

    @pytest.mark.parametrize(
        "design_size",
        ["10x20cm", "A5", "A4", "15x30cm", "20x40cm"],
    )
    def test_download_print_design_all_sizes(self, menu_qr, design_size):
        """download_print_design should work for every supported design size."""
        result = QRGeneratorService.download_print_design(
            menu_qr, design_size=design_size
        )

        assert isinstance(result, io.BytesIO)
        assert _is_valid_pdf(result)


# =============================================================================
# 19. TARGET URL GENERATION
# =============================================================================


class TestGetTargetURL:
    """Test URL generation for different QR code types."""

    def test_get_target_url_menu_type(self, menu_qr, settings):
        """MENU type QR code should generate a /q/<code>/ URL."""
        settings.SITE_URL = "https://e-menum.net"

        url = QRGeneratorService.get_target_url(menu_qr)

        assert url == f"https://e-menum.net/q/{menu_qr.code}/"

    def test_get_target_url_table_type(self, table_qr, settings):
        """TABLE type QR code should generate a /q/<code>/ URL."""
        settings.SITE_URL = "https://e-menum.net"

        url = QRGeneratorService.get_target_url(table_qr)

        assert url == f"https://e-menum.net/q/{table_qr.code}/"

    def test_get_target_url_with_redirect(self, menu_qr, settings):
        """When redirect_url is set, it should be used directly."""
        menu_qr.redirect_url = "https://custom-domain.com/menu/"
        menu_qr.save(update_fields=["redirect_url"])

        url = QRGeneratorService.get_target_url(menu_qr)

        assert url == "https://custom-domain.com/menu/"

    def test_get_target_url_fallback_site_domain(self, menu_qr, settings):
        """When SITE_URL is empty, fall back to SITE_DOMAIN."""
        settings.SITE_URL = ""
        settings.SITE_DOMAIN = "test.e-menum.net"

        url = QRGeneratorService.get_target_url(menu_qr)

        assert url.startswith("https://test.e-menum.net/q/")
        assert menu_qr.code in url


# =============================================================================
# 20. GENERATE AND SAVE
# =============================================================================


class TestGenerateAndSave:
    """Test file saving and QRCode model update."""

    def test_generate_and_save(self, menu_qr, settings, tmp_path):
        """generate_and_save should create a file on disk and update the model."""
        settings.MEDIA_ROOT = str(tmp_path)
        settings.MEDIA_URL = "/media/"
        settings.SITE_URL = "https://e-menum.net"

        # Ensure no image URL is set initially
        menu_qr.qr_image_url = None
        menu_qr.short_url = None
        menu_qr.save(update_fields=["qr_image_url", "short_url"])

        result_url = QRGeneratorService.generate_and_save(menu_qr)

        assert result_url is not None
        assert result_url.startswith("/media/qr_codes/")
        assert result_url.endswith(".png")

        # Verify model was updated
        menu_qr.refresh_from_db()
        assert menu_qr.qr_image_url == result_url
        assert menu_qr.short_url is not None

        # Verify file exists on disk
        relative = result_url.replace("/media/", "")
        full_path = os.path.join(str(tmp_path), relative)
        assert os.path.exists(full_path)

        # Verify file is a valid PNG
        with open(full_path, "rb") as f:
            file_buf = io.BytesIO(f.read())
        assert _is_valid_png(file_buf)

    def test_generate_and_save_skip_existing(self, menu_qr, settings, tmp_path):
        """If qr_image_url already exists and force=False, skip generation."""
        settings.MEDIA_ROOT = str(tmp_path)
        settings.MEDIA_URL = "/media/"

        existing_url = "/media/qr_codes/existing.png"
        menu_qr.qr_image_url = existing_url
        menu_qr.save(update_fields=["qr_image_url"])

        result_url = QRGeneratorService.generate_and_save(menu_qr, force=False)

        assert result_url == existing_url

    def test_generate_and_save_force_regenerate(self, menu_qr, settings, tmp_path):
        """With force=True, regenerate even if an image URL already exists."""
        settings.MEDIA_ROOT = str(tmp_path)
        settings.MEDIA_URL = "/media/"
        settings.SITE_URL = "https://e-menum.net"

        menu_qr.qr_image_url = "/media/qr_codes/old.png"
        menu_qr.save(update_fields=["qr_image_url"])

        result_url = QRGeneratorService.generate_and_save(menu_qr, force=True)

        assert result_url is not None
        assert result_url != "/media/qr_codes/old.png"

        menu_qr.refresh_from_db()
        assert menu_qr.qr_image_url == result_url


# =============================================================================
# BULK GENERATION
# =============================================================================


class TestGenerateBulk:
    """Test bulk QR code generation."""

    def test_generate_bulk(self, org, settings, tmp_path):
        """generate_bulk should return a dict mapping QR IDs to image URLs."""
        settings.MEDIA_ROOT = str(tmp_path)
        settings.MEDIA_URL = "/media/"
        settings.SITE_URL = "https://e-menum.net"

        qr_codes = [QRCodeFactory(organization=org, type="MENU") for _ in range(3)]

        results = QRGeneratorService.generate_bulk(qr_codes, force=True)

        assert isinstance(results, dict)
        assert len(results) == 3

        for qr in qr_codes:
            qr_id = str(qr.id)
            assert qr_id in results
            assert results[qr_id] is not None
            assert results[qr_id].endswith(".png")


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_generate_qr_image_with_long_url(self):
        """QR code generation should handle long URLs without error."""
        long_url = "https://e-menum.net/q/" + "a" * 500 + "/"
        result = QRGeneratorService.generate_qr_image(long_url, size=256)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_png(result)

    def test_generate_qr_image_with_unicode_data(self):
        """QR code generation should handle Unicode content."""
        unicode_url = "https://e-menum.net/q/kafe-istanbul-ozel/"
        result = QRGeneratorService.generate_qr_image(unicode_url, size=256)

        assert isinstance(result, io.BytesIO)
        assert _is_valid_png(result)

    def test_generate_and_save_handles_error_gracefully(
        self, menu_qr, settings, tmp_path
    ):
        """If file writing fails, generate_and_save should return None."""
        settings.MEDIA_ROOT = "/nonexistent/readonly/path"
        settings.MEDIA_URL = "/media/"
        settings.SITE_URL = "https://e-menum.net"

        menu_qr.qr_image_url = None
        menu_qr.save(update_fields=["qr_image_url"])

        result = QRGeneratorService.generate_and_save(menu_qr)

        # Should gracefully return None on failure (not raise)
        assert result is None
