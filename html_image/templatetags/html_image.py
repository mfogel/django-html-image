from django import template
from django.utils.safestring import mark_safe

register = template.Library()

IMG_TAG_FORMAT_STR = u'<img alt="{alt}" src="{src}" />'

@register.filter
def html_image_tag(html_image):
    if not html_image:
        html = u''
    # valid html req's both alt and src tags.
    html = IMG_TAG_FORMAT_STR.format(
                alt=html_image.alt_display, src=html_image.image.url)
    return mark_safe(html)
