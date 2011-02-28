from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ..models import BaseHtmlImage

register = template.Library()

@register.filter
def html_image_tag(html_image):
    if not isinstance(html_image, BaseHtmlImage):
        m = _("Given '{g}' of type {tg}, expected {te}").format(
                g=html_image, tg=type(html_image).__name__,
                te=BaseHtmlImage.__name__)
        raise TypeError(m)
    # valid html req's both alt and src tags.
    html = u'<img alt="{0}" src="{1}" />'.format(
            html_image.alt_display, html_image.image.url)
    return mark_safe(html)
