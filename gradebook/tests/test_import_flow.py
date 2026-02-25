from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


@pytest.mark.django_db
def test_import_upload_returns_preview(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")

    payload = Path(
        "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
    ).read_bytes()
    upload = SimpleUploadedFile(
        "sample.xlsx",
        payload,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response = client.post(
        reverse("import_upload"),
        data={
            "exam_name": "英语期末",
            "exam_date": "",
            "file": upload,
        },
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "导入预览" in html
    assert "学生数" in html
