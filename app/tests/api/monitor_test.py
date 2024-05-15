import pytest

from fastapi.testclient import TestClient


def test_assert_true(client: TestClient):
    assert True
