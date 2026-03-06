from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from gradebook.services.import_exam import import_exam_from_excel_bytes

DATASET_DIR = Path("测试数据集")


@pytest.mark.django_db
def test_import_upload_returns_preview(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")

    payload = (DATASET_DIR / "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx").read_bytes()
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


@pytest.mark.django_db
def test_import_upload_accepts_xls(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t2", password="p")
    assert client.login(username="t2", password="p")

    payload = (DATASET_DIR / "2025-2026学年度第一学期期末考试【八年级】-英语-八7班-单科成绩单.xls").read_bytes()
    upload = SimpleUploadedFile(
        "sample.xls",
        payload,
        content_type="application/vnd.ms-excel",
    )

    response = client.post(
        reverse("import_upload"),
        data={
            "exam_name": "英语期末-xls",
            "exam_date": "",
            "file": upload,
        },
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "导入预览" in html
    assert "学生数" in html


@pytest.mark.django_db
def test_import_upload_rejects_equivalent_exam_file(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t3", password="p")
    assert client.login(username="t3", password="p")

    first_path = DATASET_DIR / "（必）八年级英语模拟1(英语)-八年级7班.xlsx"
    second_path = DATASET_DIR / "（必）八年级英语模拟1(英语)-八年级7班(1).xlsx"

    import_exam_from_excel_bytes(
        first_path.read_bytes(),
        exam_name="英语模拟1-简表",
        exam_date=None,
        source_filename=first_path.name,
    )

    upload = SimpleUploadedFile(
        second_path.name,
        second_path.read_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response = client.post(
        reverse("import_upload"),
        data={
            "exam_name": "英语模拟1-汇总",
            "exam_date": "",
            "file": upload,
        },
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "同一场考试已导入" in html
