from os.path import join, basename

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models, IntegrityError
from django.db.models.base import ModelBase
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _


class BaseHtmlImageMetaclass(ModelBase):
    def __unicode__(self):
        return unicode(self.__name__)


class BaseHtmlImage(models.Model):
    "Basic abstract model. Derrive from me, include desired mixins."
    __metaclass__ = BaseHtmlImageMetaclass

    UNOWNED_IMAGES_DIRECTORY = 'html-images'

    alt = models.CharField(_('Alternate Text'), max_length=80, blank=True)

    # 'width' and 'height' are object properties, not actual db fields
    image = models.ImageField(_('Image'),
            width_field='width', height_field='height',
            upload_to=lambda inst,fn: inst.upload_to(fn))

    class Meta:
        abstract = True

    def __unicode__(self):
        try:
            return basename(self.image.path)
        except ValueError:
            return _('{t} (no image file)').format(t=type(self))

    @property
    def alt_display(self):
        if not self.alt:
            return self.image.name
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
            m = _("Must be connected to owner via a related field with name specified in self.owner_field_name (currently configured as '{ofn}').").format(ofn=self.owner_field_name)
            raise ImproperlyConfigured(m)

    @property
    def alt_display(self):
        """
        If alt is explicitly specified in the DB, use that.
        Elsewise, use the unicode() of the owner if it's not empty.
        If it is, then fall back on image default alt value.
        """
        if self.alt:
            return self.alt
        owner_name = unicode(getattr(self, self.owner_field_name))
        if owner_name:
            return owner_name
        return super(OwnedImageMixin, self).alt_display

    @property
    def image_directory_name(self):
        return slugify(self._meta.verbose_name)

    @property
    def owner_directory_name(self):
        return slugify(self.owner._meta.verbose_name_plural)

    def upload_to(self, org_filename):
        owner = getattr(self, self.owner_field_name)
        if owner.pk is None:
            m = _("Cannot determine where to put {t} instance's image file.  Owner has no primary key... save() owner to generate one.").format(t=type(self))
            raise IntegrityError(m)
        return join(
                self.owner_directory_name, unicode(owner.pk),
                self.image_directory_name, org_filename)


class OwnedImageToOneField(models.OneToOneField):
    "Related field from a OwnedImage to owner"

    def __init__(self, *args, **kwargs):
        disallowed_args = ('blank', 'null')
        for arg in disallowed_args:
            if kwargs.has_key(arg):
                m = _("Cannot set {a} kwarg on {s}").format(
                        a=arg, s=type(self))
                raise ImproperlyConfigured(m)
        kwargs.update({
            'blank': False,
            'null': False,
        })
        super(OwnedImageToOneField, self).__init__(*args, **kwargs)

# play well with South if it's being used
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["html_image\.models\.OwnedImageToOneField$"])
except ImportError:
    pass


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
        "Validate given image matches required size constraints."
        super(SizedImageMixin, self).clean()
        if (self.MIN_WIDTH is not None and self.width < self.MIN_WIDTH or \
            self.MAX_WIDTH is not None and self.width > self.MAX_WIDTH or \
            self.MIN_HEIGHT is not None and self.height < self.MIN_HEIGHT or \
            self.MAX_HEIGHT is not None and self.height > self.MAX_HEIGHT
        ):
            m = self._get_error_message()
            raise ValidationError(m)

    def _get_error_message(self):
        "Error message for when a image fails size vaildation."

        def get_constraint(min_req, max_req, desc):
            if min_req is not None and max_req is not None:
                if min_req is max_req:
                    constraint = _('{d}={r:n}').format(d=desc, r=min_req)
                else:
                    constraint = '{mn:n}<={d}<={mx:n}'.format(
                            mn=min_req, d=desc, mx=max_req)
            elif min_req is not None:
                constraint = _('{mn:n}<={d}').format(d=desc, mn=min_req)
            elif max_req is not None:
                constraint = _('{d}<={mx:n}').format(d=desc, mx=max_req)
            else:
                constraint = None
            return constraint

        width_cst = get_constraint(
                self.MIN_WIDTH, self.MAX_WIDTH, _('width'))
        height_cst = get_constraint(
                self.MIN_HEIGHT, self.MAX_HEIGHT, _('height'))
        full_cst = ', '.join(filter(None, (width_cst, height_cst)))

        m = _("Image does not match size constraints. Given: {gw}x{gh}, Required: {cst} (px)").format(gw=self.width, gh=self.height, cst=full_cst)
        return m
