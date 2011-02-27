from django import template
from django.utils.safestring import mark_safe

from ..models import BaseHtmlImage

register = template.Library()

@register.filter
def html_image_tag(html_image):
    if not isinstance(html_image, BaseHtmlImage):
        m = u"Given '{0}' of type {1}, expected {2}".format(
                html_image, type(html_image).__name__, BaseHtmlImage.__name__)
        raise TypeError(m)
    # valid html req's both alt and src tags.
    html = u'<img alt="{0}" src="{1}" />'.format(
            html_image.alt_display, html_image.image.url)
    return mark_safe(html)
