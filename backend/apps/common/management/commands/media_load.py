"""Read a gzipped tar of media (from media_dump) on stdin and upload to S3/MinIO.

Writes each entry to its exact key in the current default storage bucket, so
restoring into a different S3 just works. Content types are restored from the file
extension so images keep serving inline.

    cat media.tar.gz | docker compose exec -T backend python manage.py media_load
"""

import mimetypes
import sys
import tarfile

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Read a gzipped tar of media from stdin and upload to the current bucket."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Do not overwrite keys that already exist.",
        )

    def handle(self, *args, **options):
        skip_existing = options["skip_existing"]
        bucket = default_storage.bucket

        loaded, skipped = 0, 0
        with tarfile.open(fileobj=sys.stdin.buffer, mode="r|gz") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                key = member.name
                if skip_existing and default_storage.exists(key):
                    skipped += 1
                    continue
                data = tar.extractfile(member).read()
                content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
                bucket.Object(key).put(Body=data, ContentType=content_type)
                loaded += 1
                if loaded % 250 == 0:
                    self.stderr.write(f"  …{loaded} objects")

        self.stderr.write(self.style.SUCCESS(f"Loaded {loaded} objects, skipped {skipped}."))
