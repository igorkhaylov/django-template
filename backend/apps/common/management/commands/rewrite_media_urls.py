"""Rewrite absolute media URLs embedded in HTML/text fields.

FileField/ImageField values store only the storage *key*, so their URLs are
rebuilt for whatever S3 is configured — they need no rewriting. But media embedded
inside HTML/text content (rich-text bodies, descriptions, ...) holds absolute URLs
like ``https://old-host/bucket/...``. After a restore into a different S3 those must
be rewritten to the new base.

    python manage.py rewrite_media_urls --from https://old/bucket/
    python manage.py rewrite_media_urls --from <old> --to <new> --dry-run
"""

from django.apps import apps
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db.models import CharField, FileField, TextField


class Command(BaseCommand):
    help = "Replace an old media base URL with the new one across all text fields."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="old_base", required=True, help="Old media base URL.")
        parser.add_argument("--to", dest="new_base", default="", help="New base (default: current storage URL).")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        old = options["old_base"].rstrip("/") + "/"
        new = (options["new_base"].rstrip("/") if options["new_base"] else default_storage.url("").rstrip("/")) + "/"
        dry = options["dry_run"]

        if not old.startswith("http"):
            raise CommandError("--from must be an absolute URL.")
        if old == new:
            self.stdout.write(self.style.SUCCESS(f"Base unchanged ({new}); nothing to rewrite."))
            return

        self.stdout.write(f"Rewriting {old}  →  {new}")
        objs_changed, fields_changed = 0, 0

        for model in apps.get_models():
            text_fields = [
                f.name
                for f in model._meta.get_fields()
                if isinstance(f, CharField | TextField) and not isinstance(f, FileField)
            ]
            if not text_fields:
                continue
            for obj in model._base_manager.all().only("pk", *text_fields).iterator(chunk_size=500):
                dirty = []
                for fname in text_fields:
                    val = getattr(obj, fname, None)
                    if val and old in val:
                        setattr(obj, fname, val.replace(old, new))
                        dirty.append(fname)
                if dirty:
                    objs_changed += 1
                    fields_changed += len(dirty)
                    if not dry:
                        obj.save(update_fields=dirty)

        verb = "Would update" if dry else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} {fields_changed} field(s) across {objs_changed} object(s)."))
