"""S3-compatible object storage adapter — PLAN.md FASE 4.7 (EC-17).

Wraps a boto3 S3 client (works against real AWS S3 or MinIO, since MinIO
implements the S3 API). The client is injected so tests use a lightweight
fake instead of a live S3/MinIO endpoint.
"""

import os
from typing import Any, Protocol

import boto3


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


class S3StorageClient:
    def __init__(self, client: S3ClientLike, *, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/pdf",
        server_side_encryption: str | None = None,
    ) -> None:
        # F4-LOW-06: set ContentType and optional ServerSideEncryption for S3 uploads
        kwargs: dict[str, Any] = {"ContentType": content_type}
        if server_side_encryption:
            kwargs["ServerSideEncryption"] = server_side_encryption
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **kwargs)

    def generate_presigned_url(self, key: str, *, expires_in_seconds: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )

    def delete_file(self, key: str) -> None:
        # F4-LOW-04: cleanup uploaded object if downstream commit fails
        self._client.delete_object(Bucket=self._bucket, Key=key)
