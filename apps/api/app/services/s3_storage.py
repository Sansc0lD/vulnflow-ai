"""S3-compatible object storage adapter — PLAN.md FASE 4.7 (EC-17).

Wraps a boto3 S3 client (works against real AWS S3 or MinIO, since MinIO
implements the S3 API). The client is injected so tests use a lightweight
fake instead of a live S3/MinIO endpoint.
"""

import contextlib
import os
from typing import Any, Protocol

import boto3
from botocore.exceptions import ClientError


class S3ClientLike(Protocol):
    def put_object(self, *, Bucket: str, Key: str, Body: bytes, **kwargs: Any) -> Any: ...
    def generate_presigned_url(
        self, operation: str, *, Params: dict[str, str], ExpiresIn: int
    ) -> str: ...
    def delete_object(self, *, Bucket: str, Key: str, **kwargs: Any) -> Any: ...


def get_s3_bucket_name() -> str:
    bucket = os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("S3_BUCKET_NAME environment variable is not set.")
    return bucket


def make_boto_s3_client() -> S3ClientLike:
    return boto3.client(  # type: ignore[no-any-return]
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
    )


def make_public_boto_s3_client() -> S3ClientLike:
    """Create a boto3 client aimed at the browser-reachable S3/MinIO endpoint.

    Inside Docker, `S3_ENDPOINT_URL` is `http://minio:9000` (reachable by `api`
    and `worker`), which is unresolvable from the user's browser on the host.
    Presigned URL signatures include the `Host` header, so signing with
    `S3_PUBLIC_ENDPOINT_URL` (e.g. `http://localhost:9000`) ensures the browser
    can follow HTTP 307 redirects with a valid signature.
    """
    endpoint = os.environ.get("S3_PUBLIC_ENDPOINT_URL") or os.environ.get("S3_ENDPOINT_URL")
    return boto3.client(  # type: ignore[no-any-return]
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
    )


class S3StorageClient:
    def __init__(
        self,
        client: S3ClientLike,
        *,
        bucket: str,
        public_client: S3ClientLike | None = None,
    ) -> None:
        self._client = client
        self._bucket = bucket
        self._public_client = public_client or client

    def ensure_bucket_exists(self) -> None:
        head_bucket = getattr(self._client, "head_bucket", None)
        create_bucket = getattr(self._client, "create_bucket", None)
        if not callable(head_bucket) or not callable(create_bucket):
            return
        try:
            head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchBucket", "NotFound"}:
                with contextlib.suppress(ClientError):
                    create_bucket(Bucket=self._bucket)

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/pdf",
        server_side_encryption: str | None = None,
    ) -> None:
        # F4-LOW-06: set ContentType and optional ServerSideEncryption for S3 uploads
        self.ensure_bucket_exists()
        kwargs: dict[str, Any] = {"ContentType": content_type}
        if server_side_encryption:
            kwargs["ServerSideEncryption"] = server_side_encryption
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **kwargs)

    def download_bytes(self, key: str) -> tuple[bytes, str] | None:
        """Download an object directly from the internal S3/MinIO endpoint."""
        get_object = getattr(self._client, "get_object", None)
        if not callable(get_object):
            return None
        try:
            resp: Any = get_object(Bucket=self._bucket, Key=key)
        except ClientError:
            return None
        body_stream = resp.get("Body") if isinstance(resp, dict) else None
        read_fn = getattr(body_stream, "read", None)
        if not callable(read_fn):
            return None
        raw = read_fn()
        if not isinstance(raw, (bytes, bytearray)):
            return None
        content_type = str(resp.get("ContentType") or "application/octet-stream")
        return bytes(raw), content_type

    def generate_presigned_url(self, key: str, *, expires_in_seconds: int) -> str:
        return self._public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )

    def delete_file(self, key: str) -> None:
        # F4-LOW-04: cleanup uploaded object if downstream commit fails
        self._client.delete_object(Bucket=self._bucket, Key=key)
