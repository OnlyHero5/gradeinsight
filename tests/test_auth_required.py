from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_exam_list_requires_login(client) -> None:
    resp = client.get(reverse("exam_list"))
    assert resp.status_code in (301, 302)
