from os.path import join, basename

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models, IntegrityError
from django.db.models.base import ModelBase
from django.template.defaultfilters import slugify


class BaseHtmlImageMetaclass(ModelBase):
    def __unicode__(self):
        return unicode(self.__name__)


class BaseHtmlImage(models.Model):
    """
    Basic abstract model. Derrive from me, include desired mixins.

    """
    __metaclass__ = BaseHtmlImageMetaclass

    UNOWNED_IMAGES_DIRECTORY = 'html-images'

    alt = models.CharField(max_length=80, blank=True)

    # 'width' and 'height' are object properties, not actual db fields
    image = models.ImageField(width_field='width', height_field='height',
            upload_to=lambda inst,fn: inst.upload_to(fn))

    class Meta:
        abstract = True

    def __unicode__(self):
        try:
            return basename(self.image.path)
        except ValueError:
            return u'{0} (no image file)'.format(type(self), fn)

    @property
    def alt_display(self):
        return self.alt

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

    def upload_to(self, org_filename):
        return join(self.UNOWNED_IMAGES_DIRECTORY, org_filename)


class HtmlImage(BaseHtmlImage):
    """
    Basic un-owned html image. Non-abastract version of BaseHtmlIamge.

    """
    pass


class OwnedImageMixin(object):
    """
    Use this mixin with BaseHtmlImage and OwnedImageToOneField with a
    field name of self.owner_field_name.

    Override owner_directory_name and image_directory_name to customize
    where images are stored in the filesystem.  Images will be stored in:

    MEDIA_ROOT/owner_directory_name/owner.pk/image_directory_name/org_filename

    """
    owner_field_name = 'owner'

    def __init__(self, *args, **kwargs):
        super(OwnedImageMixin, self).__init__(*args, **kwargs)
        owner_field = self._meta.get_field(self.owner_field_name)
        if not isinstance(owner_field, models.ForeignKey):
            m = u"Must be connected to owner via a related field with name specified in self.owner_field_name (currently configured as '{0}').".format(self.owner_field_name)
            raise ImproperlyConfigured(m)

    @property
    def alt_display(self):
        """
        If alt is explicitly specified in the DB, use that.  Elsewise, use the
        unicode() of the owner.
        """
        return super(OwnedImageMixin, self).alt_display or \
                unicode(getattr(self, self.owner_field_name))

    @property
    def image_directory_name(self):
        return slugify(self._meta.verbose_name)

    @property
    def owner_directory_name(self):
        return slugify(self.owner._meta.verbose_name_plural)

    def upload_to(self, org_filename):
        owner = getattr(self, self.owner_field_name)
        if owner.pk is None:
            m = u"Cannot determine where to put {0} instance's image file.  Owner has no primary key... save() owner to generate one.".format(type(self))
            raise IntegrityError(m)
        return join(
                self.owner_directory_name, unicode(owner.pk),
                self.image_directory_name, org_filename)


class OwnedImageToOneField(models.OneToOneField):
    """Related field from a OwnedImage to owner"""
    def __init__(self, *args, **kwargs):
        disallowed_args = ('blank', 'null')
        for arg in disallowed_args:
            if kwargs.has_key(arg):
                m = u"Cannot set {0} kwarg on {1}".format(arg, type(self))
                raise ImproperlyConfigured(m)
        kwargs.update({
            'blank': False,
            'null': False,
        })
        super(OwnedImageToOneField, self).__init__(*args, **kwargs)


class SizedImageMixin(object):
    """
    Use this mixin with BaseHtmlImage to validate images to specific sizes.
    Override MIN_WIDTH, MAX_WIDTH, MIN_HEIGHT, and MAX_HEIGHT to
    constrain image sizes.

    """
    MIN_WIDTH = None
    MAX_WIDTH = None
    MIN_HEIGHT = None
    MAX_HEIGHT = None

    def clean(self):
        mf = u"Image {0} too {1} ({2:n}px given, {3} allowed: {4:n}px)"
        if self.MIN_WIDTH is not None and self.width < self.MIN_WIDTH:
            m = mf.format('width', 'small', self.width, 'min', self.MIN_WIDTH)
            raise ValidationError(m)
        if self.MAX_WIDTH is not None and self.width > self.MAX_WIDTH:
            m = mf.format('width', 'large', self.width, 'max', self.MAX_WIDTH)
            raise ValidationError(m)
        if self.MIN_HEIGHT is not None and self.height < self.MIN_HEIGHT:
            m = mf.format(
                    'height', 'small', self.height, 'min', self.MIN_HEIGHT)
            raise ValidationError(m)
        if self.MAX_HEIGHT is not None and self.height > self.MAX_HEIGHT:
            m = mf.format(
                    'height', 'large', self.height, 'max', self.MAX_HEIGHT)
            raise ValidationError(m)
