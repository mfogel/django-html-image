from os.path import join, basename

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models, IntegrityError
from django.db.models.base import ModelBase
from django.template.defaultfilters import slugify


class SizedImageMetaclass(ModelBase):
    def __unicode__(self):
        return unicode(self.__name__)


class SizedImage(models.Model):
    """
    Image validated to specific sizes.

    Subclass this class with another, define WIDTH_PX and HEIGHT_PX class vars.
    Set up a one-to-one field from the 'owner' of this image with
    related_name = 'owner'.
    """
    __metaclass__ = SizedImageMetaclass

    # if 'alt' is not given, unicode(self.owner) will be used in html
    alt = models.CharField(max_length=80, blank=True)

    # 'width' and 'height' are object properties, not actual db fields
    image = models.ImageField(width_field='width', height_field='height',
            upload_to=lambda inst,fn: inst.upload_to(fn))

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        required_attrs = ['WIDTH_PX', 'HEIGHT_PX']
        for attr in required_attrs:
            if not hasattr(self, attr):
                m = u'Usage: subclass %s and declare class vars %s' % \
                        (type(self), attr)
                raise ImproperlyConfigured(m)
        super(SizedImage, self).__init__(*args, **kwargs)
        # A single instance of field is shared among all instances of the same
        # model.  As such, past the first initialized instance of a model
        # this call is redunant - just overwrites related_name with same value.
        self._meta.get_field('owner').related_name = self.image_name

    def clean(self):
        if self.width != self.WIDTH_PX or self.height != self.HEIGHT_PX:
            m = u'Image dimentions must be %dx%d px (%dx%d px given)' % \
                    (self.width, self.height, self.WIDTH_PX, self.HEIGHT_PX)
            raise ValidationError(m)

    # override these to customize
    @property
    def image_name(self):
        return slugify(self._meta.verbose_name)
    @property
    def owner_name(self):
        return slugify(self.owner._meta.verbose_name_plural)

    _width = None
    def _get_width(self):
        return self._width
    def _set_width(self, val):
        self._width = val
    width = property(_get_width, _set_width)

    _height = None
    def _get_height(self):
        return self._height
    def _set_height(self, val):
        self._height = val
    height = property(_get_height, _set_height)

    def __unicode__(self):
        try:
            fn = basename(self.image.path)
        except ValueError:
            fn = '(no image file)'
        return u'%s: %s' % (type(self), fn)

    def upload_to(self, org_filename):
        if self.owner.pk is None:
            m = u"Cannot determine where to put %s instance's image file.  Owner has no primary key... save() owner to generate one." % \
                    (type(self),)
            raise IntegrityError(m)
        path_frmt = '{owner_name}/{owner_pk}/{image_name}/{org_filename}'
        return join(self.owner_name, unicode(self.owner.pk), self.image_name,
                org_filename)


class SizedImageToOneField(models.OneToOneField):
    """Related field from a SizedImage to owner"""
    def __init__(self, *args, **kwargs):
        disallowed_args = ('related_name', 'blank', 'null')
        for arg in disallowed_args:
            if kwargs.has_key(arg):
                m = u'Cannot set %s kwarg on %s' % (arg, type(self))
                raise ImproperlyConfigured(m)
        kwargs.update({
                # 'related_name' set in SizedImage.__init__
                'blank': False,
                'null': False,
            })
        super(SizedImageToOneField, self).__init__(*args, **kwargs)
