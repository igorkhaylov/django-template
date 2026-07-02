"""Block until the configured object storage (S3/MinIO) bucket is reachable.

Static AND media are served from S3/MinIO and there is no local-filesystem fallback,
so storage is a hard runtime dependency. The entrypoint runs this before
``collectstatic`` so a missing/unreachable bucket fails fast with an actionable
message instead of a cryptic boto error mid-boot.

Behaviour:
  * endpoint not reachable yet  -> retry until --timeout, then fail.
  * bucket does not exist (404) -> fail immediately (it will not appear on its own).
  * reachable + exists (or 403) -> succeed.

    python manage.py wait_for_storage [--timeout 60] [--interval 2]
"""

import time

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Wait until the S3/MinIO bucket is reachable; fail fast with a clear message if not."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=60, help="Max seconds to wait for the endpoint.")
        parser.add_argument("--interval", type=float, default=2.0, help="Seconds between attempts.")

    def handle(self, *args, **options):
        from botocore.exceptions import (
            ClientError,
            ConnectionClosedError,
            ConnectTimeoutError,
            EndpointConnectionError,
        )

        timeout = options["timeout"]
        interval = options["interval"]
        bucket_name = default_storage.bucket_name
        client = default_storage.connection.meta.client

        deadline = time.monotonic() + timeout
        attempt = 0
        while True:
            attempt += 1
            try:
                client.head_bucket(Bucket=bucket_name)
            except ClientError as exc:
                code = str(exc.response.get("Error", {}).get("Code", ""))
                if code in ("404", "NoSuchBucket"):
                    raise CommandError(
                        f"Object storage is reachable but bucket '{bucket_name}' does not exist. "
                        "Provision it first: run `make minio` for the shared local MinIO, or create "
                        "the bucket on your managed S3/MinIO provider."
                    ) from exc
                if code in ("403", "AccessDenied"):
                    # Reachable and the bucket exists, our key just can't HEAD it. Good enough.
                    self.stdout.write(
                        self.style.WARNING(f"Bucket '{bucket_name}' reachable (HEAD denied: 403) — assuming it exists.")
                    )
                    return
                raise CommandError(f"Unexpected S3 error checking bucket '{bucket_name}': {exc}") from exc
            except (EndpointConnectionError, ConnectTimeoutError, ConnectionClosedError, OSError) as exc:
                if time.monotonic() >= deadline:
                    raise CommandError(
                        f"Object storage endpoint not reachable after {timeout}s (bucket '{bucket_name}'): {exc}. "
                        "Check DJANGO_MINIO_ENDPOINT and that the S3/MinIO service is up."
                    ) from exc
                self.stdout.write(f"Waiting for object storage… (attempt {attempt})")
                time.sleep(interval)
            else:
                self.stdout.write(self.style.SUCCESS(f"Object storage bucket '{bucket_name}' is ready."))
                return
