from os.path import dirname, join

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase

from ..models import *
from ..templatetags.html_image import *


# choosing a few size constraints to test
# our test image is 75x75

class Owner(models.Model):
    name = models.CharField(max_length=255, blank=True)
    def __unicode__(self):
        return self.name

class HtmlImage(BaseHtmlImage):
    pass

class SizedImage1(SizedImageMixin, BaseHtmlImage):
    MAX_WIDTH = 50

class SizedImage2(SizedImageMixin, BaseHtmlImage):
    MIN_HEIGHT = 50
    MAX_HEIGHT = 100

class SizedImage3(SizedImageMixin, BaseHtmlImage):
    MIN_WIDTH = 50
    MAX_HEIGHT = 50

class SizedImage4(SizedImageMixin, BaseHtmlImage):
    MIN_HEIGHT = 75
    MAX_HEIGHT = 75

class OwnedImage(OwnedImageMixin, BaseHtmlImage):
    owner = OwnedImageToOneField(Owner)

class OwnedSizedImage1(OwnedImageMixin, SizedImageMixin, BaseHtmlImage):
    MAX_WIDTH = 50
    MAX_HEIGHT = 50
    owner = OwnedImageToOneField(Owner)

class OwnedSizedImage2(OwnedImageMixin, SizedImageMixin, BaseHtmlImage):
    MIN_WIDTH = 75
    MAX_WIDTH = 75
    MIN_HEIGHT = 75
    MAX_HEIGHT = 75
    owner = OwnedImageToOneField(Owner)


class HtmlImageTests(TestCase):
    image_name = 'test-img.jpg'
    image_path = join(dirname(__file__), image_name)
    image_width = 75
    image_height = 75

    alt_text = 'alt text'
    path = settings.MEDIA_URL + image_name
    owner_name = 'owner name'

    def setUp(self):
        self.image_data = open(self.image_path, 'rb').read()
        self.image = SimpleUploadedFile(self.image_name, self.image_data)

    def test_basic(self):
        i = HtmlImage(alt=self.alt_text, image=self.image)
        self.assertEqual(i.width, self.image_width)
        self.assertEqual(i.height, self.image_height)
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.alt_text, src=self.path))

        i.alt = None
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.image_name, src=self.path))

    def test_owned(self):
        with self.assertRaises(ValidationError):
            i = OwnedImage(alt='alt text', image=self.image)
            i.full_clean()

        o = Owner(name=self.owner_name)
        i = OwnedImage(alt='alt text', image=self.image, owner=o)
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.alt_text, src=self.path))

        i.alt = None
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.owner_name, src=self.path))

        o.name = ''
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.image_name, src=self.path))


    def test_sized(self):
        with self.assertRaises(ValidationError):
            i = SizedImage1(image=self.image)
            i.full_clean()

        i = SizedImage2(image=self.image)
        self.assertEqual(i.width, self.image_width)
        self.assertEqual(i.height, self.image_height)

        with self.assertRaises(ValidationError):
            i = SizedImage3(image=self.image)
            i.full_clean()

        i = SizedImage4(image=self.image)
        self.assertEqual(i.width, self.image_width)
        self.assertEqual(i.height, self.image_height)

    def test_owned_sized(self):
        with self.assertRaises(ValidationError):
            i = OwnedSizedImage1(image=self.image)
            i.full_clean()

        with self.assertRaises(ValidationError):
            i = OwnedSizedImage2(image=self.image)
            i.full_clean()

        # the full thing, most common use case too
        o = Owner(name=self.owner_name)
        i = OwnedSizedImage2(alt='alt text', image=self.image, owner=o)
        self.assertEqual(i.width, self.image_width)
        self.assertEqual(i.height, self.image_height)
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.alt_text, src=self.path))

        i.alt = None
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.owner_name, src=self.path))
