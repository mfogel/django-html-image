from django import template
from django.utils.safestring import mark_safe

from sizedimage.models import SizedImage

register = template.Library()

@register.filter
def sized_image_tag(sized_image):
    if not isinstance(sized_image, SizedImage):
        m = u'Given %s, expected %s' % \
            (sized_image.__class__.__name__, SizedImage.__name__)
        raise TypeError(m)
    alt = sized_image.alt or unicode(sized_image.owner)
    html = u'<img alt="{alt}" src="{src}" />'.format(
            alt=alt, src=sized_image.image.url)
    return mark_safe(html)
