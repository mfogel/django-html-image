from os.path import dirname, join

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import Client, TestCase

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

class OwnedImage(OwnedImageMixin, BaseHtmlImage):
    owner = OwnedImageToOneField(Owner)

class OwnedSizedImage3(SizedImageMixin, BaseHtmlImage):
    MIN_WIDTH = 50
    MIN_HEIGHT = 50

class OwnedSizedImage4(SizedImageMixin, BaseHtmlImage):
    MIN_WIDTH = 75
    MAX_WIDTH = 75
    MIN_HEIGHT = 75
    MAX_HEIGHT = 75


class HtmlImageTests(TestCase):
    image_name = 'test-img.jpg'
    image_path = join(dirname(__file__), image_name)
    image_width = 75
    image_height = 75

    alt_text = 'alt text'
    path = settings.MEDIA_URL + image_name

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
        owner_name = 'owner name'

        o = Owner(name=owner_name)
        i = OwnedImage(alt='alt text', image=self.image, owner=o)
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.alt_text, src=self.path))

        i.alt = None
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=owner_name, src=self.path))

        o.name = ''
        self.assertEqual(html_image_tag(i),
                IMG_TAG_FORMAT_STR.format(alt=self.image_name, src=self.path))


    def test_sized(self):
        pass

    def test_owned_sized(self):
        pass
