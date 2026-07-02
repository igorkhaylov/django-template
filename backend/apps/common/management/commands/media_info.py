"""Print a JSON manifest describing the media bucket.

The ``media_base_url`` it records is the key to portable restores: when media is
restored into a different S3/MinIO, the restore step rewrites embedded HTML URLs
from this base to the new one.

    docker compose exec -T backend python manage.py media_info > manifest.json
"""

import json

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

STATIC_PREFIX = "static/"


class Command(BaseCommand):
    help = "Print a JSON manifest of the media bucket (base URL, object count, bytes)."

    def add_arguments(self, parser):
        parser.add_argument("--include-static", action="store_true", help="Also count static/ objects.")

    def handle(self, *args, **options):
        include_static = options["include_static"]
        count, total = 0, 0
        for obj in default_storage.bucket.objects.all():
            if obj.key.endswith("/"):
                continue
            if not include_static and obj.key.startswith(STATIC_PREFIX):
                continue
            count += 1
            total += obj.size or 0

        manifest = {
            "media_base_url": default_storage.url("").rstrip("/") + "/",
            "object_count": count,
            "total_bytes": total,
        }
        # The manifest is the only thing on stdout — it is redirected to a file.
        self.stdout.write(json.dumps(manifest, ensure_ascii=False, indent=2))
