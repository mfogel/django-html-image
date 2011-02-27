from django import template
from django.utils.safestring import mark_safe

from ..models import SizedImage

register = template.Library()

@register.filter
def html_image_tag(html_image):
    if not isinstance(html_image, SizedImage):
        m = u'Given %s, expected %s' % \
            (type(html_image).__name__, SizedImage.__name__)
        raise TypeError(m)
    alt = html_image.alt or unicode(html_image.owner)
    html = u'<img alt="{alt}" src="{src}" />'.format(
            alt=alt, src=html_image.image.url)
    return mark_safe(html)
