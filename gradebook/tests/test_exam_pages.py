from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_exam_list_page_ok(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")

    response = client.get(reverse("exam_list"))
    assert response.status_code == 200
    assert "考试列表" in response.content.decode("utf-8")
