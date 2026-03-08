"""Populate blog post cover images with Unsplash URLs."""

from django.db import migrations


# Mapping of blog post slugs to relevant Unsplash image URLs
BLOG_COVER_IMAGES = {
    "dijital-menu-nedir-neden-gecmeli": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
    "qr-menu-ile-satis-artirma-stratejileri": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800&q=80",
    "restoran-dijitallesme-rehberi-2026": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800&q=80",
    "ai-ile-menu-yonetimi": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80",
    "alerjen-yonetimi-mevzuat-rehberi": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80",
    "ai-icerik-motoru-v2": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&q=80",
    "food-cost-kontrolu-rehberi": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&q=80",
    "coklu-sube-yonetimi-ipuclari": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
    "musteri-deneyimi-dijital-menu": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80",
    "pos-entegrasyonu-rehberi": "https://images.unsplash.com/photo-1556742111-a301076d9d18?w=800&q=80",
    "sektor-trendleri-2026": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
    "e-menum-basari-hikayesi-cafe-mola": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80",
}


def populate_cover_images(apps, schema_editor):
    BlogPost = apps.get_model("website", "BlogPost")
    for slug, url in BLOG_COVER_IMAGES.items():
        BlogPost.objects.filter(slug=slug).update(cover_image_url=url)


def clear_cover_images(apps, schema_editor):
    BlogPost = apps.get_model("website", "BlogPost")
    BlogPost.objects.filter(slug__in=BLOG_COVER_IMAGES.keys()).update(
        cover_image_url=""
    )


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0012_blogpost_cover_image_url"),
    ]

    operations = [
        migrations.RunPython(populate_cover_images, clear_cover_images),
    ]
