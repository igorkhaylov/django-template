"""Integration tests for the django-stdimage fork (User.picture).

Cover the full lifecycle against the in-memory test storage: variation rendering
on save, variation attributes on fresh instances, django-cleanup file removal,
and the fork's DRF ``StdImageSerializer`` (read, write and validation) — the
serializer ships untested upstream, so the template owns this coverage.
"""

import io

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from PIL import Image
from rest_framework import serializers
from stdimage.serializers import StdImageSerializer

from users.models import User

# Default variations of the fork's StdImageField (see DEFAULT_VARIATIONS).
VARIATION_NAMES = ("thumbnail", "small", "medium", "large")


def jpeg_upload(name="avatar.jpg", size=(1200, 900)) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.fixture
def user_with_picture(user):
    user.picture = jpeg_upload()
    user.save()
    return user


def variation_size(field_file, variation_name):
    """Open a rendered variation from storage and return its (width, height)."""
    name = field_file.field.attr_class.get_variation_name(field_file.name, variation_name)
    with field_file.storage.open(name) as f, Image.open(f) as img:
        return img.size


@pytest.mark.django_db
class TestStdImageField:
    def test_save_renders_all_default_variations(self, user_with_picture):
        picture = user_with_picture.picture
        for name in VARIATION_NAMES:
            variation = getattr(picture, name)
            assert picture.storage.exists(variation.name)
            assert variation.name.endswith(f".{name}.webp")

    def test_thumbnail_is_cropped_to_square(self, user_with_picture):
        assert variation_size(user_with_picture.picture, "thumbnail") == (100, 100)

    def test_proportional_variation_keeps_aspect_ratio(self, user_with_picture):
        # 1200x900 -> small is capped at width 400 -> 400x300.
        assert variation_size(user_with_picture.picture, "small") == (400, 300)

    def test_variation_larger_than_source_is_not_upscaled(self, user_with_picture):
        # large targets width 1920; the 1200x900 source must stay untouched.
        assert variation_size(user_with_picture.picture, "large") == (1200, 900)

    def test_variations_available_on_instance_loaded_from_db(self, user_with_picture):
        fresh = User.objects.get(pk=user_with_picture.pk)
        for name in VARIATION_NAMES:
            assert getattr(fresh.picture, name).url

    def test_blank_picture_is_falsy(self, user):
        assert not user.picture

    def test_cleanup_deletes_original_and_variations(self, user_with_picture, django_capture_on_commit_callbacks):
        picture = user_with_picture.picture
        names = [picture.name] + [getattr(picture, name).name for name in VARIATION_NAMES]
        # django-cleanup removes files in a transaction.on_commit hook.
        with django_capture_on_commit_callbacks(execute=True):
            user_with_picture.delete()
        for name in names:
            assert not default_storage.exists(name)


class UserPictureSerializer(serializers.ModelSerializer):
    picture = StdImageSerializer(required=False)

    class Meta:
        model = User
        fields = ("id", "picture")


@pytest.mark.django_db
class TestStdImageSerializer:
    def test_representation_contains_original_and_all_variations(self, user_with_picture):
        data = UserPictureSerializer(user_with_picture).data
        assert set(data["picture"]) == {"original", *VARIATION_NAMES}
        assert data["picture"]["original"].endswith(".jpg")
        for name in VARIATION_NAMES:
            assert data["picture"][name].endswith(f".{name}.webp")

    def test_null_picture_serializes_to_none(self, user):
        assert UserPictureSerializer(user).data["picture"] is None

    def test_upload_through_serializer_renders_variations(self, user):
        serializer = UserPictureSerializer(instance=user, data={"picture": jpeg_upload()}, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        for name in VARIATION_NAMES:
            assert updated.picture.storage.exists(getattr(updated.picture, name).name)
        assert set(serializer.data["picture"]) == {"original", *VARIATION_NAMES}

    def test_upload_rejects_non_image(self, user):
        broken = SimpleUploadedFile("not-an-image.txt", b"plain text", content_type="text/plain")
        serializer = UserPictureSerializer(instance=user, data={"picture": broken}, partial=True)
        assert not serializer.is_valid()
        assert "picture" in serializer.errors
