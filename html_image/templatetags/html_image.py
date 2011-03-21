from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ..models import BaseHtmlImage

register = template.Library()

@register.filter
def html_image_tag(html_image):
    # valid html req's both alt and src tags.
    try:
        html = u'<img alt="{0}" src="{1}" />'.format(
                html_image.alt_display, html_image.image.url)
    except:
        html = u''
    return mark_safe(html)
