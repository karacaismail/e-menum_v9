"""
Google Tag Manager integration for E-Menum.

Provides GTMManager class that generates GTM script snippets
for <head> and <body> tags, and dataLayer push scripts.
"""

import json

from django.conf import settings
from django.utils.safestring import mark_safe


class GTMManager:
    """
    Google Tag Manager snippet generator.

    Generates the required GTM JavaScript snippets for page templates.
    Uses settings.SEO_GTM_CONTAINER_ID by default, or accepts a custom ID.
    """

    def __init__(self, gtm_id=None):
        self.gtm_id = gtm_id or getattr(settings, "SEO_GTM_CONTAINER_ID", "")

    def get_head_snippet(self):
        """
        Return the GTM script tag for insertion in <head>.

        Returns an empty string if no GTM container ID is configured.
        """
        if not self.gtm_id:
            return ""

        snippet = (
            "<!-- Google Tag Manager -->\n"
            "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n"
            "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n"
            "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n"
            "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n"
            "})(window,document,'script','dataLayer','" + self.gtm_id + "');</script>\n"
            "<!-- End Google Tag Manager -->"
        )
        return mark_safe(snippet)

    def get_body_snippet(self):
        """
        Return the GTM noscript tag for insertion immediately after <body>.

        Returns an empty string if no GTM container ID is configured.
        """
        if not self.gtm_id:
            return ""

        snippet = (
            "<!-- Google Tag Manager (noscript) -->\n"
            '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id='
            + self.gtm_id
            + '"\n'
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
            "<!-- End Google Tag Manager (noscript) -->"
        )
        return mark_safe(snippet)

    def get_datalayer(self, **kwargs):
        """
        Return a dataLayer.push() script tag with the given key-value data.

        Usage:
            gtm.get_datalayer(event='page_view', page_type='menu')

        Returns a mark_safe string containing the <script> tag.
        Returns an empty string if no data is provided.
        """
        if not kwargs:
            return ""

        data_json = json.dumps(kwargs, ensure_ascii=False)
        snippet = (
            "<script>"
            "window.dataLayer = window.dataLayer || []; "
            "dataLayer.push(" + data_json + ");"
            "</script>"
        )
        return mark_safe(snippet)
