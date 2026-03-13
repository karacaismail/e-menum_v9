"""
Schema.org JSON-LD builder classes for structured data.

Provides builder classes that accept Django model instances and produce
valid JSON-LD ``<script>`` blocks for embedding in HTML templates.

Builders:
    SchemaBuilder            - Abstract base with to_dict / to_json_ld
    OrganizationSchema       - From SiteSettings
    ArticleSchema            - From BlogPost
    FAQPageSchema            - From FAQ queryset
    BreadcrumbListSchema     - From list of (name, url) tuples
    LocalBusinessSchema      - From SiteSettings + address
    WebPageSchema            - Generic web page
    ProductSchema            - For pricing plans
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.utils.safestring import mark_safe

logger = logging.getLogger("apps.seo")


# ──────────────────────────────────────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────────────────────────────────────


class SchemaBuilder:
    """
    Abstract base class for Schema.org JSON-LD builders.

    Subclasses must implement ``to_dict`` which returns a plain Python dict
    representing the JSON-LD object.  ``to_json_ld`` wraps the dict inside a
    ``<script type="application/ld+json">`` tag that is safe for template
    rendering.
    """

    schema_type: str = "Thing"

    def _base_context(self) -> Dict[str, Any]:
        """Return the ``@context`` and ``@type`` envelope."""
        return {
            "@context": "https://schema.org",
            "@type": self.schema_type,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return the structured-data payload as a plain dict.

        Subclasses **must** override this method.
        """
        raise NotImplementedError("Subclasses must implement to_dict()")

    def to_json_ld(self) -> str:
        """
        Return a safe ``<script type="application/ld+json">`` string.

        The output is marked safe so Django templates can render it directly
        without escaping.
        """
        data = self.to_dict()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return mark_safe(f'<script type="application/ld+json">\n{json_str}\n</script>')

    @staticmethod
    def _clean(value: Any) -> Optional[str]:
        """Return stripped string or ``None`` if empty/falsy."""
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None


# ──────────────────────────────────────────────────────────────────────────────
# OrganizationSchema
# ──────────────────────────────────────────────────────────────────────────────


class OrganizationSchema(SchemaBuilder):
    """
    Build an ``Organization`` JSON-LD from a
    :class:`apps.website.models.SiteSettings` instance.
    """

    schema_type = "Organization"

    def __init__(self, site_settings) -> None:
        """
        Parameters
        ----------
        site_settings:
            A ``SiteSettings`` model instance.
        """
        self.settings = site_settings

    def to_dict(self) -> Dict[str, Any]:
        s = self.settings
        data = self._base_context()
        data["name"] = self._clean(s.company_name) or "E-Menum"
        if self._clean(s.description):
            data["description"] = self._clean(s.description)
        if self._clean(s.phone):
            data["telephone"] = self._clean(s.phone)
        if self._clean(s.email):
            data["email"] = self._clean(s.email)
        if self._clean(s.address):
            data["address"] = {
                "@type": "PostalAddress",
                "addressLocality": self._clean(s.address),
            }

        # Social profiles
        same_as = []
        for attr in (
            "social_instagram",
            "social_twitter",
            "social_linkedin",
            "social_youtube",
        ):
            url = self._clean(getattr(s, attr, ""))
            if url:
                same_as.append(url)
        if same_as:
            data["sameAs"] = same_as

        # Contact point
        if self._clean(s.phone) or self._clean(s.email):
            contact_point = {
                "@type": "ContactPoint",
                "contactType": "customer service",
            }
            if self._clean(s.phone):
                contact_point["telephone"] = self._clean(s.phone)
            if self._clean(s.email):
                contact_point["email"] = self._clean(s.email)
            data["contactPoint"] = contact_point

        return data


# ──────────────────────────────────────────────────────────────────────────────
# ArticleSchema
# ──────────────────────────────────────────────────────────────────────────────


class ArticleSchema(SchemaBuilder):
    """
    Build an ``Article`` JSON-LD from a
    :class:`apps.website.models.BlogPost` instance.
    """

    schema_type = "Article"

    def __init__(self, blog_post, *, base_url: str = "") -> None:
        """
        Parameters
        ----------
        blog_post:
            A ``BlogPost`` model instance.
        base_url:
            Absolute scheme + host prefix (e.g. ``https://e-menum.net``).
        """
        self.post = blog_post
        self.base_url = base_url.rstrip("/")

    def to_dict(self) -> Dict[str, Any]:
        p = self.post
        data = self._base_context()
        data["headline"] = self._clean(p.title) or ""
        if self._clean(p.excerpt):
            data["description"] = self._clean(p.excerpt)

        # URL
        if p.slug:
            data["url"] = f"{self.base_url}/blog/{p.slug}/"
            data["mainEntityOfPage"] = {
                "@type": "WebPage",
                "@id": data["url"],
            }

        # Dates
        if p.published_at:
            data["datePublished"] = p.published_at.isoformat()
        if hasattr(p, "updated_at") and p.updated_at:
            data["dateModified"] = p.updated_at.isoformat()

        # Author
        author_name = self._clean(getattr(p, "author_name", ""))
        if author_name:
            data["author"] = {
                "@type": "Person",
                "name": author_name,
            }

        # Image
        og_url = ""
        if hasattr(p, "get_og_image_url"):
            og_url = p.get_og_image_url()
        if og_url:
            data["image"] = (
                f"{self.base_url}{og_url}" if og_url.startswith("/") else og_url
            )

        # Publisher (generic)
        data["publisher"] = {
            "@type": "Organization",
            "name": "E-Menum",
        }

        # Word count estimate (rough)
        content = self._clean(p.content) or ""
        if content:
            data["wordCount"] = len(content.split())

        return data


# ──────────────────────────────────────────────────────────────────────────────
# FAQPageSchema
# ──────────────────────────────────────────────────────────────────────────────


class FAQPageSchema(SchemaBuilder):
    """
    Build a ``FAQPage`` JSON-LD from a queryset (or iterable) of FAQ objects.

    Each FAQ object must have ``question`` and ``answer`` attributes.
    """

    schema_type = "FAQPage"

    def __init__(self, faq_queryset) -> None:
        """
        Parameters
        ----------
        faq_queryset:
            An iterable of FAQ model instances.
        """
        self.faqs = faq_queryset

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        main_entities: List[Dict[str, Any]] = []
        for faq in self.faqs:
            question = self._clean(faq.question)
            answer = self._clean(faq.answer)
            if question and answer:
                main_entities.append(
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer,
                        },
                    }
                )
        data["mainEntity"] = main_entities
        return data


# ──────────────────────────────────────────────────────────────────────────────
# BreadcrumbListSchema
# ──────────────────────────────────────────────────────────────────────────────


class BreadcrumbListSchema(SchemaBuilder):
    """
    Build a ``BreadcrumbList`` JSON-LD from a list of ``(name, url)`` tuples.

    Example::

        crumbs = [('Home', '/'), ('Blog', '/blog/'), ('Post Title', '/blog/my-post/')]
        schema = BreadcrumbListSchema(crumbs)
    """

    schema_type = "BreadcrumbList"

    def __init__(self, crumbs: List[Tuple[str, str]]) -> None:
        """
        Parameters
        ----------
        crumbs:
            Ordered list of ``(name, url)`` tuples from root to current page.
        """
        self.crumbs = crumbs

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        items: List[Dict[str, Any]] = []
        for position, (name, url) in enumerate(self.crumbs, start=1):
            items.append(
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": name,
                    "item": url,
                }
            )
        data["itemListElement"] = items
        return data


# ──────────────────────────────────────────────────────────────────────────────
# LocalBusinessSchema
# ──────────────────────────────────────────────────────────────────────────────


class LocalBusinessSchema(SchemaBuilder):
    """
    Build a ``LocalBusiness`` JSON-LD from a
    :class:`apps.website.models.SiteSettings` instance.

    Extends the basic organisation data with geographic / opening-hours
    fields suitable for a local listing.
    """

    schema_type = "LocalBusiness"

    def __init__(
        self,
        site_settings,
        *,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        price_range: str = "",
        opening_hours: Optional[List[str]] = None,
    ) -> None:
        """
        Parameters
        ----------
        site_settings:
            A ``SiteSettings`` model instance.
        latitude / longitude:
            Optional geo coordinates.
        price_range:
            E.g. ``"$$"`` or ``"TL 50-200"``.
        opening_hours:
            List of opening-hours specs (schema.org format), e.g.
            ``["Mo-Fr 09:00-22:00", "Sa 10:00-23:00"]``.
        """
        self.settings = site_settings
        self.latitude = latitude
        self.longitude = longitude
        self.price_range = price_range
        self.opening_hours = opening_hours

    def to_dict(self) -> Dict[str, Any]:
        s = self.settings
        data = self._base_context()
        data["name"] = self._clean(s.company_name) or "E-Menum"
        if self._clean(s.description):
            data["description"] = self._clean(s.description)
        if self._clean(s.phone):
            data["telephone"] = self._clean(s.phone)
        if self._clean(s.email):
            data["email"] = self._clean(s.email)

        # Address
        if self._clean(s.address):
            data["address"] = {
                "@type": "PostalAddress",
                "addressLocality": self._clean(s.address),
                "addressCountry": "TR",
            }

        # Geo
        if self.latitude is not None and self.longitude is not None:
            data["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": self.latitude,
                "longitude": self.longitude,
            }

        # Price range
        if self._clean(self.price_range):
            data["priceRange"] = self.price_range

        # Opening hours
        if self.opening_hours:
            data["openingHours"] = self.opening_hours

        # Social profiles
        same_as = []
        for attr in (
            "social_instagram",
            "social_twitter",
            "social_linkedin",
            "social_youtube",
        ):
            url = self._clean(getattr(s, attr, ""))
            if url:
                same_as.append(url)
        if same_as:
            data["sameAs"] = same_as

        return data


# ──────────────────────────────────────────────────────────────────────────────
# WebPageSchema
# ──────────────────────────────────────────────────────────────────────────────


class WebPageSchema(SchemaBuilder):
    """
    Build a generic ``WebPage`` JSON-LD.

    Can be used for any marketing page that does not have a more specific
    schema type.
    """

    schema_type = "WebPage"

    def __init__(
        self,
        *,
        name: str = "",
        description: str = "",
        url: str = "",
        breadcrumbs: Optional[List[Tuple[str, str]]] = None,
        date_published: Optional[str] = None,
        date_modified: Optional[str] = None,
        in_language: str = "tr",
    ) -> None:
        self.name = name
        self.description = description
        self.url = url
        self.breadcrumbs = breadcrumbs
        self.date_published = date_published
        self.date_modified = date_modified
        self.in_language = in_language

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        if self._clean(self.name):
            data["name"] = self._clean(self.name)
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.url):
            data["url"] = self._clean(self.url)
            data["@id"] = self._clean(self.url)
        if self.in_language:
            data["inLanguage"] = self.in_language
        if self.date_published:
            data["datePublished"] = self.date_published
        if self.date_modified:
            data["dateModified"] = self.date_modified

        # Embed breadcrumbs when provided
        if self.breadcrumbs:
            breadcrumb_schema = BreadcrumbListSchema(self.breadcrumbs)
            data["breadcrumb"] = breadcrumb_schema.to_dict()

        # Publisher
        data["publisher"] = {
            "@type": "Organization",
            "name": "E-Menum",
        }

        return data


# ──────────────────────────────────────────────────────────────────────────────
# ProductSchema
# ──────────────────────────────────────────────────────────────────────────────


class ProductSchema(SchemaBuilder):
    """
    Build a ``Product`` JSON-LD suitable for pricing plan display.

    Parameters map to a subscription plan's customer-facing attributes.
    """

    schema_type = "Product"

    def __init__(
        self,
        *,
        name: str = "",
        description: str = "",
        price: Optional[float] = None,
        currency: str = "TRY",
        url: str = "",
        sku: str = "",
        brand: str = "E-Menum",
        availability: str = "https://schema.org/InStock",
        price_valid_until: str = "",
    ) -> None:
        self.name = name
        self.description = description
        self.price = price
        self.currency = currency
        self.url = url
        self.sku = sku
        self.brand = brand
        self.availability = availability
        self.price_valid_until = price_valid_until

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        if self._clean(self.name):
            data["name"] = self._clean(self.name)
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.sku):
            data["sku"] = self._clean(self.sku)
        if self._clean(self.brand):
            data["brand"] = {
                "@type": "Brand",
                "name": self._clean(self.brand),
            }

        # Offers
        if self.price is not None:
            offer: Dict[str, Any] = {
                "@type": "Offer",
                "price": str(self.price),
                "priceCurrency": self.currency,
                "availability": self.availability,
            }
            if self._clean(self.url):
                offer["url"] = self._clean(self.url)
            if self._clean(self.price_valid_until):
                offer["priceValidUntil"] = self._clean(self.price_valid_until)
            data["offers"] = offer

        return data


# ──────────────────────────────────────────────────────────────────────────────
# WebSiteSchema — with SiteLinksSearchBox
# ──────────────────────────────────────────────────────────────────────────────


class WebSiteSchema(SchemaBuilder):
    """
    Build a ``WebSite`` JSON-LD with optional sitelinks search box.

    Used on the homepage to enable Google's sitelinks search box feature.
    """

    schema_type = "WebSite"

    def __init__(
        self,
        name: str,
        url: str,
        *,
        search_url_template: Optional[str] = None,
        description: Optional[str] = None,
        alternate_name: Optional[str] = None,
    ) -> None:
        self.name = name
        self.url = url
        self.search_url_template = search_url_template
        self.description = description
        self.alternate_name = alternate_name

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        data["name"] = self.name
        data["url"] = self.url
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.alternate_name):
            data["alternateName"] = self._clean(self.alternate_name)
        if self.search_url_template:
            data["potentialAction"] = {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": self.search_url_template,
                },
                "query-input": "required name=search_term_string",
            }
        return data


# ──────────────────────────────────────────────────────────────────────────────
# HowToSchema
# ──────────────────────────────────────────────────────────────────────────────


class HowToSchema(SchemaBuilder):
    """
    Build a ``HowTo`` JSON-LD from a list of steps.

    Used for tutorial or how-to content pages.
    """

    schema_type = "HowTo"

    def __init__(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, str]]] = None,
        total_time: Optional[str] = None,
        image: Optional[str] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.steps = steps or []
        self.total_time = total_time
        self.image = image

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        data["name"] = self.name
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.total_time):
            data["totalTime"] = self._clean(self.total_time)
        if self._clean(self.image):
            data["image"] = self._clean(self.image)
        if self.steps:
            data["step"] = [
                {
                    "@type": "HowToStep",
                    "position": i + 1,
                    "name": step.get("name", ""),
                    "text": step.get("text", ""),
                    **({"image": step["image"]} if step.get("image") else {}),
                }
                for i, step in enumerate(self.steps)
            ]
        return data


# ──────────────────────────────────────────────────────────────────────────────
# ReviewSchema
# ──────────────────────────────────────────────────────────────────────────────


class ReviewSchema(SchemaBuilder):
    """Build a ``Review`` JSON-LD for customer reviews."""

    schema_type = "Review"

    def __init__(
        self,
        item_name: str,
        *,
        author_name: str = "",
        rating_value: Optional[float] = None,
        best_rating: float = 5,
        review_body: Optional[str] = None,
        date_published: Optional[str] = None,
    ) -> None:
        self.item_name = item_name
        self.author_name = author_name
        self.rating_value = rating_value
        self.best_rating = best_rating
        self.review_body = review_body
        self.date_published = date_published

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        data["itemReviewed"] = {"@type": "Thing", "name": self.item_name}
        if self._clean(self.author_name):
            data["author"] = {"@type": "Person", "name": self._clean(self.author_name)}
        if self.rating_value is not None:
            data["reviewRating"] = {
                "@type": "Rating",
                "ratingValue": self.rating_value,
                "bestRating": self.best_rating,
            }
        if self._clean(self.review_body):
            data["reviewBody"] = self._clean(self.review_body)
        if self._clean(self.date_published):
            data["datePublished"] = self._clean(self.date_published)
        return data


# ──────────────────────────────────────────────────────────────────────────────
# EventSchema
# ──────────────────────────────────────────────────────────────────────────────


class EventSchema(SchemaBuilder):
    """Build an ``Event`` JSON-LD for webinars and events."""

    schema_type = "Event"

    def __init__(
        self,
        name: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        location_name: Optional[str] = None,
        location_url: Optional[str] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        organizer_name: Optional[str] = None,
        event_attendance_mode: str = "https://schema.org/OnlineEventAttendanceMode",
        event_status: str = "https://schema.org/EventScheduled",
    ) -> None:
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.location_name = location_name
        self.location_url = location_url
        self.description = description
        self.image = image
        self.organizer_name = organizer_name
        self.event_attendance_mode = event_attendance_mode
        self.event_status = event_status

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        data["name"] = self.name
        data["eventAttendanceMode"] = self.event_attendance_mode
        data["eventStatus"] = self.event_status
        if self._clean(self.start_date):
            data["startDate"] = self._clean(self.start_date)
        if self._clean(self.end_date):
            data["endDate"] = self._clean(self.end_date)
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.image):
            data["image"] = self._clean(self.image)
        if self._clean(self.organizer_name):
            data["organizer"] = {
                "@type": "Organization",
                "name": self._clean(self.organizer_name),
            }
        if self._clean(self.location_name) or self._clean(self.location_url):
            location: Dict[str, Any] = {"@type": "VirtualLocation"}
            if self._clean(self.location_url):
                location["url"] = self._clean(self.location_url)
            if self._clean(self.location_name):
                location["name"] = self._clean(self.location_name)
            data["location"] = location
        return data


# ──────────────────────────────────────────────────────────────────────────────
# VideoObjectSchema
# ──────────────────────────────────────────────────────────────────────────────


class VideoObjectSchema(SchemaBuilder):
    """Build a ``VideoObject`` JSON-LD for video content."""

    schema_type = "VideoObject"

    def __init__(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        upload_date: Optional[str] = None,
        duration: Optional[str] = None,
        content_url: Optional[str] = None,
        embed_url: Optional[str] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.upload_date = upload_date
        self.duration = duration
        self.content_url = content_url
        self.embed_url = embed_url

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        data["name"] = self.name
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.thumbnail_url):
            data["thumbnailUrl"] = self._clean(self.thumbnail_url)
        if self._clean(self.upload_date):
            data["uploadDate"] = self._clean(self.upload_date)
        if self._clean(self.duration):
            data["duration"] = self._clean(self.duration)
        if self._clean(self.content_url):
            data["contentUrl"] = self._clean(self.content_url)
        if self._clean(self.embed_url):
            data["embedUrl"] = self._clean(self.embed_url)
        return data


# ──────────────────────────────────────────────────────────────────────────────
# JobPostingSchema
# ──────────────────────────────────────────────────────────────────────────────


class JobPostingSchema(SchemaBuilder):
    """Build a ``JobPosting`` JSON-LD for career pages."""

    schema_type = "JobPosting"

    def __init__(
        self,
        title: str,
        *,
        description: Optional[str] = None,
        date_posted: Optional[str] = None,
        valid_through: Optional[str] = None,
        employment_type: Optional[str] = None,
        hiring_organization_name: Optional[str] = None,
        job_location_name: Optional[str] = None,
        remote: bool = False,
    ) -> None:
        self.title = title
        self.description = description
        self.date_posted = date_posted
        self.valid_through = valid_through
        self.employment_type = employment_type
        self.hiring_organization_name = hiring_organization_name
        self.job_location_name = job_location_name
        self.remote = remote

    def to_dict(self) -> Dict[str, Any]:
        data = self._base_context()
        data["title"] = self.title
        if self._clean(self.description):
            data["description"] = self._clean(self.description)
        if self._clean(self.date_posted):
            data["datePosted"] = self._clean(self.date_posted)
        if self._clean(self.valid_through):
            data["validThrough"] = self._clean(self.valid_through)
        if self._clean(self.employment_type):
            data["employmentType"] = self._clean(self.employment_type)
        if self._clean(self.hiring_organization_name):
            data["hiringOrganization"] = {
                "@type": "Organization",
                "name": self._clean(self.hiring_organization_name),
            }
        if self.remote:
            data["jobLocationType"] = "TELECOMMUTE"
        elif self._clean(self.job_location_name):
            data["jobLocation"] = {
                "@type": "Place",
                "address": self._clean(self.job_location_name),
            }
        return data
