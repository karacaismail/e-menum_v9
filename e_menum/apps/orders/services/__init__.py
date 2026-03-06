"""
Services for the Orders application.

Provides QR code generation and other order-related services.
"""

from apps.orders.services.qr_generator import QRGeneratorService

__all__ = ['QRGeneratorService']
