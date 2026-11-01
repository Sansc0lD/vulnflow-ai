"""PLAN.md FASE 4.7 — S3/MinIO object storage adapter (EC-17 presigned URL regen)."""

from typing import Any

from app.services.s3_storage import S3StorageClient


class _FakeBotoClient:
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}
        self.last_kwargs: dict[str, Any] = {}
        self.presign_calls: list[tuple[str, str, int]] = []
        self.deleted_keys: list[str] = []

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, **kwargs: Any) -> None:
        self.uploaded[f"{Bucket}/{Key}"] = Body
        self.last_kwargs = kwargs

    def generate_presigned_url(
        self, operation: str, *, Params: dict[str, str], ExpiresIn: int
    ) -> str:
        self.presign_calls.append((Params["Bucket"], Params["Key"], ExpiresIn))
        return f"https://minio.local/{Params['Bucket']}/{Params['Key']}?expires={ExpiresIn}"

    def delete_object(self, *, Bucket: str, Key: str, **kwargs: Any) -> None:
        self.uploaded.pop(f"{Bucket}/{Key}", None)
        self.deleted_keys.append(f"{Bucket}/{Key}")


def test_upload_bytes_stores_content_at_bucket_and_key() -> None:
    boto_client = _FakeBotoClient()
    storage = S3StorageClient(boto_client, bucket="vulnflow-reports")

    storage.upload_bytes("reports/prj-1/report.pdf", b"%PDF-1.4 fake pdf bytes")

    assert boto_client.uploaded["vulnflow-reports/reports/prj-1/report.pdf"] == (
        b"%PDF-1.4 fake pdf bytes"
    )
    assert boto_client.last_kwargs.get("ContentType") == "application/pdf"


def test_generate_presigned_url_returns_fresh_url_with_requested_ttl() -> None:
    # EC-17: the download proxy regenerates a fresh presigned URL each time
    # rather than reusing a possibly-expired one.
    boto_client = _FakeBotoClient()
    storage = S3StorageClient(boto_client, bucket="vulnflow-reports")

    url = storage.generate_presigned_url("reports/prj-1/report.pdf", expires_in_seconds=900)

    assert url == "https://minio.local/vulnflow-reports/reports/prj-1/report.pdf?expires=900"
    assert boto_client.presign_calls == [("vulnflow-reports", "reports/prj-1/report.pdf", 900)]


def test_delete_file_deletes_object() -> None:
    boto_client = _FakeBotoClient()
    storage = S3StorageClient(boto_client, bucket="vulnflow-reports")

    storage.upload_bytes("reports/prj-1/report.pdf", b"%PDF-1.4 fake pdf bytes")
    assert "vulnflow-reports/reports/prj-1/report.pdf" in boto_client.uploaded

    storage.delete_file("reports/prj-1/report.pdf")
    assert "vulnflow-reports/reports/prj-1/report.pdf" not in boto_client.uploaded
    assert boto_client.deleted_keys == ["vulnflow-reports/reports/prj-1/report.pdf"]
